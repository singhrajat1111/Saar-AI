import structlog
from typing import Dict, Any
import pandas as pd
import numpy as np
from app.core.reliability_helper import ReliabilityHelper

logger = structlog.get_logger()

class MLAgent:
    """
    Agent responsible for recommending suitable Machine Learning models
    based on the dataset schema and EDA statistics.
    Does NOT train the model yet, just identifies the best ML approaches.
    """
    
    def __init__(self, schema_data: Dict[str, Any], eda_data: Dict[str, Any]):
        self.schema = schema_data
        self.eda = eda_data

    def execute(self) -> Dict[str, Any]:
        logger.info("ml_agent_start")
        
        try:
            recommendations = []
            features = []
            potential_targets = []
            
            # Retrieve rows from eda_data
            total_rows = self.eda.get("quality", {}).get("total_rows", 0)
            assessment = ReliabilityHelper.assess(total_rows)

            # Simple heuristic: Look for columns with "target", "label", "price", "is_", "has_"
            schema_list = self.schema.get("schema", [])
            for col_info in schema_list:
                col_name = col_info["column_name"].lower()
                sem_type = col_info["semantic_type"]
                
                if sem_type == "numeric":
                    features.append(col_info["column_name"])
                    if any(keyword in col_name for keyword in ["price", "cost", "revenue", "amount", "total"]):
                        potential_targets.append({
                            "column": col_info["column_name"],
                            "task": "Regression",
                            "suggested_models": ["Linear Regression", "Random Forest Regressor", "XGBoost"]
                        })
                elif sem_type == "categorical":
                    features.append(col_info["column_name"])
                    if col_info["unique_values"] == 2 or any(keyword in col_name for keyword in ["is_", "has_", "status", "category"]):
                        potential_targets.append({
                            "column": col_info["column_name"],
                            "task": "Classification",
                            "suggested_models": ["Logistic Regression", "Random Forest Classifier", "LightGBM"]
                        })

            if not assessment.can_model:
                action_str = " ".join(f"{i+1}) {action}" for i, action in enumerate(assessment.recommended_actions))
                reasoning = (
                    "Modeling is not recommended due to dataset limitations. "
                    "This dataset does not contain sufficient statistical reliability for predictive modeling. "
                    f"Limitations: {assessment.explanation} Recommended action: {action_str}"
                )
                recommendations = [{
                    "task": "Data Collection / Sample Expansion Required",
                    "suggested_models": [],
                    "reasoning": reasoning
                }]
                potential_targets = []
            else:
                if not potential_targets:
                     recommendations.append({
                         "task": "Clustering / Unsupervised Learning",
                         "suggested_models": ["K-Means", "DBSCAN", "PCA"],
                         "reasoning": "No obvious target variable detected. Clustering can help find hidden segments."
                     })
                 
            logger.info("ml_agent_success")
            return {
                "status": "success",
                "potential_features": features,
                "potential_targets": potential_targets,
                "unsupervised_recommendations": recommendations if not potential_targets or not assessment.can_model else []
            }
        except Exception as e:
            logger.error("ml_agent_error", error=str(e))
            return {"status": "failed", "reason": str(e)}
