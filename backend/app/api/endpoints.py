import os
import uuid
import structlog
import asyncio
import json
from typing import Dict, List, Any
from fastapi import APIRouter, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException, Response
from fastapi.responses import FileResponse
import pandas as pd
import redis.asyncio as aioredis

from app.workers.pipeline import process_dataset
from app.core.dataset_store import DatasetStore
from app.agents.cleaning_agent import CleaningAgent
from app.agents.schema_agent import SchemaAgent
from app.agents.eda_agent import EDAAgent
from app.agents.ml_agent import MLAgent
from app.agents.llm_agent import LLMAgent
from app.agents.visualization_agent import VisualizationAgent
from app.core.report_builder import ReportBuilder

logger = structlog.get_logger()
router = APIRouter()

REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    raise RuntimeError(
        "REDIS_URL environment variable is required. Configure Upstash Redis before starting SAAR AI."
    )

# Simple in-memory fallback connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def broadcast_local(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception as e:
                logger.error("failed_to_send_local_message", client_id=client_id, error=str(e))

manager = ConnectionManager()

@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...), client_id: str = "demo_client"):
    """
    Receives the uploaded file, saves it, registers it in the DatasetStore,
    and processes the dataset synchronously.
    """
    filename = file.filename or "dataset.csv"
    logger.info("api_upload_start", filename=filename)
    
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".csv", ".xlsx", ".xls"]:
        raise HTTPException(status_code=400, detail="Unsupported file format. Must be CSV or Excel.")
    
    # Save file temporarily
    temp_dir = "/tmp/saar_ai_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"{uuid.uuid4()}{ext}")
    
    try:
        with open(temp_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                buffer.write(chunk)
                
        # Register the dataset in local store
        dataset_id = DatasetStore.register_dataset(filename, temp_path)
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
                
    dataset = DatasetStore.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=500, detail="Failed to register dataset.")
    persisted_path = dataset["file_path"]
    
    # Process dataset synchronously
    result = process_dataset(persisted_path, client_id, dataset_id)
    
    return {
        "status": "completed",
        "dataset_id": dataset_id,
        "filename": filename,
        "result": result
    }

@router.get("/datasets")
def list_datasets():
    """
    Returns list of all uploaded datasets.
    """
    return DatasetStore.get_all_datasets()

@router.get("/datasets/{dataset_id}")
def get_dataset_details(dataset_id: str):
    """
    Returns all metadata and profile results for a dataset.
    """
    dataset = DatasetStore.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset

@router.get("/datasets/{dataset_id}/preview")
def get_dataset_preview(dataset_id: str):
    """
    Returns the first 100 rows of the dataset as a list of dictionaries for table preview.
    """
    try:
        df = DatasetStore.get_dataframe(dataset_id)
        # Select first 100 rows
        preview_df = df.head(100)
        # Handle non-JSON serializable values like NaN
        preview_df = preview_df.replace({pd.NA: None, float('nan'): None})
        
        return {
            "columns": df.columns.tolist(),
            "data": preview_df.to_dict(orient="records"),
            "total_rows": len(df)
        }
    except KeyError:
        raise HTTPException(status_code=404, detail="Dataset not found")
    except Exception as e:
        logger.error("preview_failed", dataset_id=dataset_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/datasets/{dataset_id}/clean")
async def clean_dataset(dataset_id: str, payload: Dict[str, Any]):
    """
    Applies selected cleaning operations, re-runs statistical profiling,
    saves the cleaned dataset, and updates the registry.
    """
    logger.info("api_clean_dataset_start", dataset_id=dataset_id)
    
    dataset = DatasetStore.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    operations = payload.get("operations", [])
    if not operations:
        return dataset
        
    try:
        # Load df
        df = DatasetStore.get_dataframe(dataset_id)
        
        # Apply cleaning ops
        cleaner = CleaningAgent()
        cleaned_df = cleaner.apply_operations(df, operations)
        
        # Re-run profiles
        schema_res = SchemaAgent(cleaned_df).execute()
        if schema_res["status"] == "failed":
            raise HTTPException(status_code=500, detail=f"Schema inference failed: {schema_res.get('reason')}")
            
        eda_res = EDAAgent(cleaned_df).execute()
        if eda_res["status"] == "failed":
            raise HTTPException(status_code=500, detail=f"EDA calculation failed: {eda_res.get('reason')}")
            
        # Re-detect issues
        cleaning_rec = cleaner.detect_issues(schema_res.get("schema", []), eda_res)
        
        # Re-run ML recommendation
        ml_res = MLAgent(schema_res, eda_res).execute()
        
        # Re-run visualizations
        viz_res = VisualizationAgent(cleaned_df, schema_res.get("schema", []), eda_res).execute()
        viz_charts = viz_res.get("recommended_charts", []) if viz_res["status"] == "success" else []
        
        # Re-run LLM insights (which supports fallback)
        llm_res = LLMAgent(schema_res, eda_res, ml_res).execute()
        
        # Save dataframe
        DatasetStore.save_dataframe(dataset_id, cleaned_df)
        
        # Record cleaning operation history
        history = dataset.get("cleaning_history", [])
        history.append({
            "timestamp": pd.Timestamp.now().isoformat(),
            "operations": operations
        })
        
        # Update registry
        DatasetStore.update_dataset(dataset_id, {
            "rows_count": len(cleaned_df),
            "columns_count": len(cleaned_df.columns),
            "missing_values_count": int(cleaned_df.isnull().sum().sum()),
            "duplicates_count": int(cleaned_df.duplicated().sum()),
            "schema": schema_res.get("schema", []),
            "eda": eda_res,
            "cleaning_recommendations": cleaning_rec,
            "cleaning_history": history,
            "ml_recommendations": ml_res,
            "visualizations": viz_charts,
            "ai_insights": llm_res
        })
        
        updated_dataset = DatasetStore.get_dataset(dataset_id)
        return updated_dataset
        
    except Exception as e:
        logger.error("cleaning_endpoint_failed", dataset_id=dataset_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Exception during cleaning: {str(e)}")

@router.get("/datasets/{dataset_id}/download")
def download_dataset(dataset_id: str):
    """
    Downloads the dataset file.
    """
    dataset = DatasetStore.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    file_path = dataset["file_path"]
    filename = dataset["filename"]
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Physical file not found")
        
    return FileResponse(file_path, filename=filename, media_type="application/octet-stream")

@router.get("/datasets/{dataset_id}/report")
def get_dataset_report(dataset_id: str, format: str = "html", report_type: str = "technical"):
    """
    Generates and returns the analytical report in HTML, PDF, Markdown, or JSON.
    """
    dataset = DatasetStore.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    fmt = format.lower().strip()
    rtype = report_type.lower().strip()
    if rtype not in ("technical", "executive"):
        rtype = "technical"
        
    filename = dataset.get("filename", "dataset")
    base_name = os.path.splitext(filename)[0]
    
    from app.core.reports.data_compiler import compile_report_data, generate_filename
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    
    out_filename = generate_filename(base_name, rtype, fmt, now)
    
    if fmt == "html":
        from app.core.reports.html_renderer import render_technical, render_executive
        data = compile_report_data(dataset, rtype)
        html_content = render_executive(data) if rtype == "executive" else render_technical(data)
        return Response(
            content=html_content,
            media_type="text/html",
            headers={"Content-Disposition": f"attachment; filename={out_filename}"}
        )
    elif fmt == "pdf":
        from app.core.reports.pdf_renderer import render_technical, render_executive
        data = compile_report_data(dataset, rtype)
        pdf_bytes = render_executive(data) if rtype == "executive" else render_technical(data)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={out_filename}"}
        )
    elif fmt in ("markdown", "md"):
        from app.core.reports.markdown_renderer import render_technical, render_executive
        data = compile_report_data(dataset, rtype)
        md_content = render_executive(data) if rtype == "executive" else render_technical(data)
        return Response(
            content=md_content,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename={out_filename}"}
        )
    elif fmt == "json":
        from app.core.reports.json_renderer import render_json
        data = compile_report_data(dataset, rtype)
        json_content = render_json(data)
        return Response(
            content=json_content,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={out_filename}"}
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Supported formats are html, pdf, markdown, json.")

@router.post("/ai/explain")
def explain_insight(payload: dict):
    """
    On-demand AI explanation endpoint. Accepts a JSON request with:
    - type: string (e.g. recommendation, chart, statistical_test, executive_summary, quality_score, insight, report)
    - level: string (beginner, intermediate, expert)
    - payload: dict (the structured statistical JSON)
    - dataset_id: string (optional, the active dataset ID)
    """
    explanation_type = payload.get("type")
    level = payload.get("level", "intermediate")
    data = payload.get("payload")
    dataset_id = payload.get("dataset_id")

    if not explanation_type or data is None:
        raise HTTPException(status_code=400, detail="Missing required fields: 'type' and 'payload' must be provided.")

    try:
        from app.services.ai.explanation_service import ExplanationService
        result = ExplanationService.explain(explanation_type, level, data, dataset_id)
        return result
    except Exception as e:
        logger.error("ai_explain_endpoint_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/{client_id}")

async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for the Live Analysis Timeline.
    Subscribes to Redis Pub/Sub for worker tasks, sending updates to client.
    """
    await websocket.accept()
    logger.info("ws_client_connected", client_id=client_id)
    
    # Establish connection to Redis
    pubsub = None
    redis_client = None
    try:
        redis_client = aioredis.Redis.from_url(REDIS_URL, decode_responses=True)
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(f"saar_channel_{client_id}")
        logger.info("ws_redis_subscribed", channel=f"saar_channel_{client_id}")
    except Exception as e:
        logger.error("ws_redis_connection_failed", error=str(e))
        # Fallback to local ConnectionManager
        await manager.connect(websocket, client_id)
        
    async def listen_redis():
        if not pubsub:
            return
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message["type"] == "message":
                    data = message["data"] if isinstance(message["data"], str) else message["data"].decode("utf-8")
                    await websocket.send_text(data)
                    logger.debug("ws_sent_from_redis", client_id=client_id, data=data)
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("ws_listen_redis_error", error=str(e))

    # Start redis listening task
    redis_task = None
    if pubsub:
        redis_task = asyncio.create_task(listen_redis())

    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            logger.debug("ws_client_msg", client_id=client_id, data=data)
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        logger.info("ws_client_disconnected", client_id=client_id)
    finally:
        if redis_task:
            redis_task.cancel()
        if pubsub:
            await pubsub.unsubscribe(f"saar_channel_{client_id}")
            await pubsub.close()
        if redis_client:
            await redis_client.aclose()
        manager.disconnect(client_id)
