import os
import json
import redis
import pandas as pd
import structlog

from app.agents.validation_agent import ValidationAgent
from app.agents.schema_agent import SchemaAgent
from app.agents.eda_agent import EDAAgent
from app.agents.ml_agent import MLAgent
from app.agents.llm_agent import LLMAgent
from app.agents.cleaning_agent import CleaningAgent
from app.agents.visualization_agent import VisualizationAgent
from app.core.dataset_store import DatasetStore
from app.core.dataset_validator import ValidationErrorModel, ValidationCode, VALIDATOR_VERSION

from typing import Optional, Dict, Any

logger = structlog.get_logger()
REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    raise RuntimeError(
        "REDIS_URL environment variable is required. Configure Upstash Redis before starting SAAR AI."
    )

def broadcast_update(client_id: str, step: str, status: str, message: str = "", type_: str = "timeline_update", results: Optional[dict] = None):
    """
    Publishes a status message to the Redis Pub/Sub channel for the client.
    """
    try:
        r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        payload: Dict[str, Any] = {
            "type": type_,
            "step": step,
            "status": status,
            "message": message,
            "validation_duration_ms": None,
            "error_code": None,
            "validator_version": None,
        }
        if results is not None:
            payload["results"] = results
            payload["validation_duration_ms"] = results.get("validation_duration_ms")
            payload["error_code"] = results.get("error_code")
            payload["validator_version"] = results.get("validator_version")
            
        r.publish(f"saar_channel_{client_id}", json.dumps(payload))
        logger.info("broadcast_published", client_id=client_id, step=step, status=status)
    except Exception as e:
        logger.error("broadcast_publish_failed", error=str(e))

def process_dataset_task(file_path: str, client_id: str, dataset_id: Optional[str] = None):
    """
    The Core Workflow Engine Pipeline.
    Chains the execution of all intelligent agents sequentially.
    """
    import time
    logger.info("workflow_started", file_path=file_path, dataset_id=dataset_id)
    
    if dataset_id:
        DatasetStore.update_dataset(dataset_id, {"status": "processing"})
        
    try:
        # Determine format from file path extension
        ext = os.path.splitext(file_path)[1].lower()
        file_type = ext.replace(".", "")
        
        # 1. Validation
        broadcast_update(client_id, "Validation", "processing")
        start_time = time.time()
        validation = ValidationAgent(file_path, file_type=file_type).execute()
        duration_ms = int((time.time() - start_time) * 1000)
        
        if validation["status"] == "failed":
            error_obj = validation.get("error_object")
            broadcast_update(
                client_id, 
                "Validation", 
                "failed", 
                message=error_obj.get("message") if error_obj else "Validation failed",
                results={
                    "error_object": error_obj,
                    "validation_duration_ms": duration_ms,
                    "error_code": error_obj.get("code") if error_obj else None,
                    "validator_version": error_obj.get("version", VALIDATOR_VERSION) if error_obj else VALIDATOR_VERSION
                }
            )
            if dataset_id and error_obj:
                DatasetStore.update_dataset(dataset_id, {
                    "status": "failed",
                    "validation_failed": True,
                    "validation_code": error_obj.get("code"),
                    "validation_message": error_obj.get("message"),
                    "failed_step": "validation",
                    "failed_at": pd.Timestamp.now().isoformat(),
                    "validator_version": error_obj.get("version", VALIDATOR_VERSION),
                    "validation_duration_ms": duration_ms
                })
            return {"status": "failed", "step": "validation", "error_object": error_obj}
            
        broadcast_update(
            client_id,
            "Validation",
            "completed",
            results={
                "validation_duration_ms": duration_ms,
                "error_code": None,
                "validator_version": VALIDATOR_VERSION,
            },
        )
        
        # Extract quality warnings (informational only)
        warnings = validation.get("metadata", {}).get("warnings", [])
        
        # Load Dataframe once validated
        if dataset_id:
            df = DatasetStore.get_dataframe(dataset_id)
        else:
            if file_type == "csv":
                df = pd.read_csv(file_path)
            elif file_type in ["xlsx", "xls"]:
                engine = 'openpyxl' if file_type == 'xlsx' else 'xlrd'
                df = pd.read_excel(file_path, engine=engine)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        
        # 2. Schema Detection
        broadcast_update(client_id, "Schema Detection", "processing")
        schema = SchemaAgent(df).execute()
        if schema["status"] == "failed":
            broadcast_update(client_id, "Schema Detection", "failed", schema.get("reason", ""))
            return schema
        broadcast_update(client_id, "Schema Detection", "completed")
        
        # 3. EDA & Statistics
        broadcast_update(client_id, "EDA & Statistics", "processing")
        eda = EDAAgent(df).execute()
        if eda["status"] == "failed":
            broadcast_update(client_id, "EDA & Statistics", "failed", eda.get("reason", ""))
            return eda
        broadcast_update(client_id, "EDA & Statistics", "completed")
        
        # 3.5. Data Cleaning Detection
        cleaning_rec = CleaningAgent().detect_issues(schema.get("schema", []), eda)
        
        # 4. ML Recommendation
        broadcast_update(client_id, "ML Recommendation", "processing")
        ml = MLAgent(schema, eda).execute()
        if ml["status"] == "failed":
            broadcast_update(client_id, "ML Recommendation", "failed", ml.get("reason", ""))
            return ml
        broadcast_update(client_id, "ML Recommendation", "completed")
        
        # 4.5. Visualization Recommendations
        broadcast_update(client_id, "Visualizations", "processing")
        viz = VisualizationAgent(df, schema.get("schema", []), eda).execute()
        broadcast_update(client_id, "Visualizations", "completed")
        
        # 5. LLM Prompting & Insight Generation
        broadcast_update(client_id, "AI Insight Generation", "processing")
        llm = LLMAgent(schema, eda, ml).execute()
        if llm["status"] == "failed":
            broadcast_update(client_id, "AI Insight Generation", "failed", llm.get("reason", ""))
            return llm
        
        # Inject Warnings into AI insights report object
        if isinstance(llm, dict):
            llm["dataset_warnings"] = warnings
            
        broadcast_update(client_id, "AI Insight Generation", "completed")
        
        # 6. Feature Store Sync (Dummy status step)
        broadcast_update(client_id, "Feature Store Sync", "completed")
        
        results = {
            "schema": schema.get("schema", []),
            "eda": eda,
            "cleaning_recommendations": cleaning_rec,
            "ml_recommendations": ml,
            "visualizations": viz.get("recommended_charts", []) if viz["status"] == "success" else [],
            "ai_insights": llm,
            "warnings": warnings
        }
        
        # Complete & Save to Registry
        if dataset_id:
            num_rows = len(df)
            num_cols = len(df.columns)
            missing_count = int(df.isnull().sum().sum())
            duplicates_count = int(df.duplicated().sum())
            
            DatasetStore.update_dataset(dataset_id, {
                "status": "completed",
                "rows_count": num_rows,
                "columns_count": num_cols,
                "missing_values_count": missing_count,
                "duplicates_count": duplicates_count,
                "schema": schema.get("schema", []),
                "eda": eda,
                "cleaning_recommendations": cleaning_rec,
                "ml_recommendations": ml,
                "visualizations": viz.get("recommended_charts", []) if viz["status"] == "success" else [],
                "ai_insights": llm,
                "warnings": warnings
            })
            
        logger.info("workflow_completed", file_path=file_path)
        
        # Broadcast workflow complete event with the final results
        broadcast_update(client_id, "", "", type_="workflow_complete", results=results)
        
        return {
            "status": "success",
            "results": results
        }
        
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error("workflow_fatal_error", error=str(e), traceback=tb)
        
        unexpected_error = ValidationErrorModel(
            code=ValidationCode.UNEXPECTED_PIPELINE_ERROR,
            message="An unexpected server error occurred during data processing.",
            severity="critical",
            recoverable=True
        ).model_dump()
        
        broadcast_update(
            client_id, 
            "Pipeline", 
            "failed", 
            message=str(unexpected_error.get("message", "An unexpected server error occurred.")), 
            results={"error_object": unexpected_error}
        )
        
        if dataset_id:
            DatasetStore.update_dataset(dataset_id, {
                "status": "failed",
                "validation_failed": True,
                "validation_code": unexpected_error.get("code"),
                "validation_message": unexpected_error.get("message"),
                "failed_step": "pipeline",
                "failed_at": pd.Timestamp.now().isoformat(),
                "validator_version": "1.0",
                "error_message": str(e)
            })
            
        return {
            "status": "failed", 
            "error_object": unexpected_error
        }
