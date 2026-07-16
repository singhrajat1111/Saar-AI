import pandas as pd
import numpy as np
import structlog
from typing import Dict, Any, List

logger = structlog.get_logger()

class SchemaAgent:
    """
    Agent responsible for detecting and structuring the schema of a dataset.
    It infers column types and identifies semantic types (numeric, categorical,
    boolean, datetime, identifier, text).
    """
    
    def __init__(self, dataframe: pd.DataFrame):
        self.df = dataframe

    def _infer_semantic_type(self, col: str, series: pd.Series) -> str:
        # Get data type
        dtype = series.dtype
        n_unique = series.nunique()
        n_total = len(series)
        
        if n_total == 0:
            return "categorical"
            
        # 1. Check for Datetime
        if pd.api.types.is_datetime64_any_dtype(dtype):
            return "datetime"
            
        # If object/string, try to see if it parses as date
        if pd.api.types.is_object_dtype(dtype) or pd.api.types.is_string_dtype(dtype):
            # Sample a few non-null values to verify date parsing
            non_nulls = series.dropna().head(10)
            if not non_nulls.empty:
                try:
                    # If it parses as date, check if it fits date criteria
                    parsed = pd.to_datetime(non_nulls, errors='coerce')
                    if parsed.notnull().all():
                        return "datetime"
                except Exception:
                    pass
                    
        # 2. Check for Boolean (including categorical representations)
        if pd.api.types.is_bool_dtype(dtype):
            return "boolean"
            
        if n_unique == 2:
            unique_vals = [str(x).lower().strip() for x in series.dropna().unique()]
            boolean_sets = [
                {"0", "1"}, {"0.0", "1.0"}, {"false", "true"}, 
                {"f", "t"}, {"no", "yes"}, {"n", "y"}
            ]
            for b_set in boolean_sets:
                if set(unique_vals).issubset(b_set):
                    return "boolean"

        # 3. Check for Numeric
        if pd.api.types.is_numeric_dtype(dtype):
            # Float or Int with many unique values, or if column name suggests numeric
            return "numeric"

        # 4. Check for Text vs Identifier vs Categorical
        if pd.api.types.is_object_dtype(dtype) or pd.api.types.is_string_dtype(dtype):
            # Check unique ratio
            unique_ratio = n_unique / n_total
            
            # Compute average string length of non-nulls
            non_null_strs = series.dropna().astype(str)
            if not non_null_strs.empty:
                avg_len = non_null_strs.str.len().mean()
            else:
                avg_len = 0
                
            if avg_len > 50:
                return "text"
            elif unique_ratio > 0.90:
                return "identifier"
            else:
                return "categorical"
                
        return "categorical"

    def execute(self) -> Dict[str, Any]:
        logger.info("schema_agent_start", columns=len(self.df.columns))
        
        try:
            schema_info = []
            for col in self.df.columns:
                series = self.df[col]
                dtype_name = str(series.dtype)
                semantic_type = self._infer_semantic_type(col, series)
                
                schema_info.append({
                    "column_name": col,
                    "pandas_dtype": dtype_name,
                    "semantic_type": semantic_type,
                    "unique_values": int(series.nunique()),
                    "null_count": int(series.isnull().sum()),
                    "null_percentage": round(float(series.isnull().sum() / len(self.df) * 100), 2) if len(self.df) > 0 else 0.0
                })
                
            logger.info("schema_agent_success", schema_size=len(schema_info))
            return {
                "status": "success",
                "schema": schema_info
            }
        except Exception as e:
            logger.error("schema_agent_error", error=str(e))
            return {"status": "failed", "reason": str(e)}
