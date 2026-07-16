import pandas as pd
import numpy as np
import structlog
from typing import Dict, List, Any

logger = structlog.get_logger()

class CleaningAgent:
    """
    Agent responsible for detecting data quality issues, recommending actionable fixes,
    and executing data cleaning operations on a dataset.
    """
    
    def __init__(self, dataframe: pd.DataFrame = None):
        self.df = dataframe

    def detect_issues(self, schema_data: List[Dict[str, Any]], eda_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyzes schema and EDA statistics to compile recommended cleaning operations.
        """
        recommendations = []
        
        # 1. Duplicate rows
        duplicates = eda_data.get("quality", {}).get("duplicate_rows", 0)
        if duplicates > 0:
            recommendations.append({
                "id": "drop_duplicates",
                "type": "drop_duplicates",
                "column": None,
                "issue": f"The dataset contains {duplicates} duplicate rows.",
                "recommendation": "Remove duplicate records to prevent skewed analysis.",
                "severity": "medium"
            })
            
        # 2. Empty or Constant columns
        empty_cols = eda_data.get("quality", {}).get("empty_columns", [])
        for col in empty_cols:
            recommendations.append({
                "id": f"drop_empty_{col}",
                "type": "drop_columns",
                "column": col,
                "issue": f"Column '{col}' is entirely empty (100% missing).",
                "recommendation": f"Drop empty column '{col}' from the dataset.",
                "severity": "high",
                "columns": [col]
            })
            
        constant_cols = eda_data.get("quality", {}).get("constant_columns", [])
        for col in constant_cols:
            if col not in empty_cols:  # avoid duplicate warning
                recommendations.append({
                    "id": f"drop_constant_{col}",
                    "type": "drop_columns",
                    "column": col,
                    "issue": f"Column '{col}' has a constant value across all records.",
                    "recommendation": f"Drop constant column '{col}' since it provides no variance for analysis.",
                    "severity": "low",
                    "columns": [col]
                })

        # 3. Missing values in columns
        for col_info in schema_data:
            col_name = col_info["column_name"]
            null_count = col_info["null_count"]
            null_pct = col_info["null_percentage"]
            semantic_type = col_info["semantic_type"]
            
            # Skip empty or constant columns which are handled above
            if col_name in empty_cols or col_name in constant_cols:
                continue
                
            if null_count > 0:
                strategy = "mode" if semantic_type in ["categorical", "boolean", "identifier"] else "median"
                recommendations.append({
                    "id": f"impute_{col_name}",
                    "type": "impute_missing",
                    "column": col_name,
                    "issue": f"Column '{col_name}' has {null_count} missing values ({null_pct}%).",
                    "recommendation": f"Impute missing values using the {strategy} value.",
                    "severity": "medium" if null_pct < 30 else "high",
                    "default_strategy": strategy
                })

        # 4. Outliers (numeric columns)
        numeric_stats = eda_data.get("numeric_stats", {})
        for col, stats_info in numeric_stats.items():
            outliers_count = stats_info.get("outliers_count", 0)
            outliers_pct = stats_info.get("outliers_pct", 0)
            
            if outliers_count > 0:
                recommendations.append({
                    "id": f"handle_outliers_{col}",
                    "type": "handle_outliers",
                    "column": col,
                    "issue": f"Column '{col}' has {outliers_count} outliers ({outliers_pct}% of values).",
                    "recommendation": "Clip outliers to the 1.5x IQR upper and lower bounds.",
                    "severity": "low" if outliers_pct < 5 else "medium"
                })

        return recommendations

    def apply_operations(self, df: pd.DataFrame, operations: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Applies a list of user-selected data cleaning operations to the DataFrame.
        """
        # Create a deep copy to prevent mutating the original until saved
        cleaned_df = df.copy()
        
        for op in operations:
            op_type = op.get("type")
            column = op.get("column")
            
            logger.info("apply_cleaning_op", type=op_type, column=column)
            
            if op_type == "drop_duplicates":
                cleaned_df = cleaned_df.drop_duplicates()
                
            elif op_type == "drop_columns":
                cols_to_drop = op.get("columns", [])
                if column and column not in cols_to_drop:
                    cols_to_drop.append(column)
                # Filter to only existing columns
                cols_to_drop = [c for c in cols_to_drop if c in cleaned_df.columns]
                if cols_to_drop:
                    cleaned_df = cleaned_df.drop(columns=cols_to_drop)
                    
            elif op_type == "impute_missing":
                if not column or column not in cleaned_df.columns:
                    continue
                strategy = op.get("strategy", "median")
                series = cleaned_df[column]
                
                if series.isnull().sum() == 0:
                    continue
                    
                if strategy == "mean":
                    fill_value = series.mean()
                elif strategy == "median":
                    fill_value = series.median()
                elif strategy == "mode":
                    mode_series = series.mode()
                    fill_value = mode_series.iloc[0] if not mode_series.empty else None
                elif strategy == "value":
                    fill_value = op.get("fill_value")
                else:
                    fill_value = None
                    
                if fill_value is not None:
                    cleaned_df[column] = cleaned_df[column].fillna(fill_value)
                    
            elif op_type == "handle_outliers":
                if not column or column not in cleaned_df.columns:
                    continue
                # IQR clipping
                series = cleaned_df[column]
                q25 = series.quantile(0.25)
                q75 = series.quantile(0.75)
                iqr = q75 - q25
                lower_bound = q25 - 1.5 * iqr
                upper_bound = q75 + 1.5 * iqr
                cleaned_df[column] = cleaned_df[column].clip(lower=lower_bound, upper=upper_bound)
                
            elif op_type == "cast_types":
                if not column or column not in cleaned_df.columns:
                    continue
                target_type = op.get("target_type")
                try:
                    if target_type == "numeric":
                        cleaned_df[column] = pd.to_numeric(cleaned_df[column], errors='coerce')
                    elif target_type == "categorical":
                        cleaned_df[column] = cleaned_df[column].astype(str)
                    elif target_type == "datetime":
                        cleaned_df[column] = pd.to_datetime(cleaned_df[column], errors='coerce')
                except Exception as e:
                    logger.error("cast_type_failed", column=column, target_type=target_type, error=str(e))
                    
        return cleaned_df
