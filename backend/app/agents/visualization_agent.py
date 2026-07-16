import pandas as pd
import numpy as np
import structlog
from typing import Dict, Any, List

logger = structlog.get_logger()

class VisualizationAgent:
    """
    Agent responsible for recommending and compiling data payloads for charts.
    Produces clean, pre-binned, or pre-formatted JSON data for Histograms,
    Bar Charts, Scatter Plots, Correlation Heatmaps, and Line Charts over time.
    """
    
    def __init__(self, df: pd.DataFrame, schema_info: List[Dict[str, Any]], eda_info: Dict[str, Any]):
        self.df = df
        self.schema = schema_info
        self.eda = eda_info

    def _compile_histogram(self, col: str) -> Dict[str, Any]:
        series = self.df[col].dropna()
        if series.empty:
            return {}
            
        try:
            # Filter to finite values only
            series = series[np.isfinite(series)]
            if series.empty:
                return {}
                
            # Determine number of bins dynamically (between 5 and 20)
            n_unique = series.nunique()
            bins_count = min(15, max(5, int(np.sqrt(len(series)))))
            if n_unique < bins_count:
                bins_count = n_unique
                
            bins_count = max(1, bins_count)
            counts, bin_edges = np.histogram(series, bins=bins_count)
            chart_data = []
            for i in range(len(counts)):
                label = f"{round(bin_edges[i], 1)} - {round(bin_edges[i+1], 1)}"
                chart_data.append({
                    "bin": label,
                    "count": int(counts[i])
                })
                
            return {
                "type": "histogram",
                "title": f"Distribution of {col}",
                "x_axis": col,
                "y_axis": "Frequency Count",
                "data": chart_data,
                "column": col,
                "description": f"Histogram showing the frequency distribution and value spread of {col}."
            }
        except Exception as e:
            logger.error("failed_to_build_histogram", column=col, error=str(e))
            return {}

    def _compile_bar_chart(self, col: str) -> Dict[str, Any]:
        series = self.df[col].dropna()
        if series.empty:
            return {}
            
        # Get top categories from EDA if possible
        cat_stats = self.eda.get("categorical_stats", {}).get(col, {})
        top_cats = cat_stats.get("top_categories", [])
        
        if not top_cats:
            # Calculate manually
            value_counts = series.value_counts().head(10)
            top_cats = [{"value": str(k), "count": int(v)} for k, v in value_counts.items()]
            
        chart_data = [{"category": x["value"], "count": x["count"]} for x in top_cats]
        
        return {
            "type": "bar",
            "title": f"Value Counts of {col}",
            "x_axis": col,
            "y_axis": "Count",
            "data": chart_data,
            "column": col,
            "description": f"Bar chart showing the frequency count for the top categories of {col}."
        }

    def _compile_scatter_plot(self, col1: str, col2: str) -> Dict[str, Any]:
        temp_df = self.df[[col1, col2]].dropna()
        if temp_df.empty:
            return {}
            
        # Downsample if dataset is large to prevent clogging the DOM
        if len(temp_df) > 300:
            temp_df = temp_df.sample(n=300, random_state=42)
            
        chart_data = []
        for _, row in temp_df.iterrows():
            try:
                x_val = float(row[col1])
                y_val = float(row[col2])
                if not np.isnan(x_val) and not np.isinf(x_val) and not np.isnan(y_val) and not np.isinf(y_val):
                    chart_data.append({
                        "x": x_val,
                        "y": y_val
                    })
            except Exception:
                pass
            
        return {
            "type": "scatter",
            "title": f"{col1} vs {col2} Scatter Plot",
            "x_axis": col1,
            "y_axis": col2,
            "data": chart_data,
            "description": f"Scatter plot displaying the relationship and correlation pattern between '{col1}' and '{col2}'."
        }

    def _compile_heatmap(self) -> Dict[str, Any]:
        corr_data = self.eda.get("correlations", {})
        matrix = corr_data.get("matrix", {})
        if not matrix:
            return {}
            
        chart_data = []
        # Recharts expects a list of points or a flat table structure
        for col1, row in matrix.items():
            for col2, val in row.items():
                try:
                    val_float = float(val) if val is not None else 0.0
                    if np.isnan(val_float) or np.isinf(val_float):
                        val_float = 0.0
                except Exception:
                    val_float = 0.0
                    
                chart_data.append({
                    "x": col1,
                    "y": col2,
                    "value": val_float
                })
                
        return {
            "type": "heatmap",
            "title": "Feature Correlation Heatmap",
            "data": chart_data,
            "description": "Pearson correlation coefficient matrix between numeric features. Values range from -1 (perfect negative) to +1 (perfect positive)."
        }

    def _compile_line_chart(self, date_col: str, num_col: str) -> Dict[str, Any]:
        try:
            temp_df = self.df[[date_col, num_col]].dropna()
            if temp_df.empty:
                return {}
                
            # Parse date
            temp_df[date_col] = pd.to_datetime(temp_df[date_col], errors='coerce')
            temp_df = temp_df.dropna(subset=[date_col])
            
            # Sort by date
            temp_df = temp_df.sort_values(by=date_col)
            
            # If there are too many records, aggregate by month/day
            n_rows = len(temp_df)
            if len(temp_df) > 100:
                # Group by date part depending on span
                date_span = (temp_df[date_col].max() - temp_df[date_col].min()).days
                if date_span > 365 * 2:
                    # group by year-month
                    temp_df["group_date"] = temp_df[date_col].dt.to_period("M").astype(str)
                elif date_span > 60:
                    # group by week
                    temp_df["group_date"] = temp_df[date_col].dt.to_period("W").astype(str)
                else:
                    # group by day
                    temp_df["group_date"] = temp_df[date_col].dt.to_period("D").astype(str)
                    
                grouped = temp_df.groupby("group_date")[num_col].mean().reset_index()
                
                chart_data = []
                for _, row in grouped.iterrows():
                    val = float(row[num_col])
                    if not np.isnan(val) and not np.isinf(val):
                        chart_data.append({"date": row["group_date"], "value": val})
            else:
                chart_data = []
                for _, row in temp_df.iterrows():
                    val = float(row[num_col])
                    if not np.isnan(val) and not np.isinf(val):
                        chart_data.append({"date": row[date_col].strftime("%Y-%m-%d"), "value": val})
                
            return {
                "type": "line",
                "title": f"Trend of {num_col} over time",
                "x_axis": date_col,
                "y_axis": num_col,
                "data": chart_data,
                "description": f"Line chart showing temporal trend and changes in '{num_col}' grouped by '{date_col}'."
            }
        except Exception as e:
            logger.error("failed_to_build_line_chart", date_col=date_col, num_col=num_col, error=str(e))
            return {}

    def execute(self) -> Dict[str, Any]:
        logger.info("visualization_agent_start")
        recommended_charts = []
        
        try:
            # Identify columns by semantic type
            numeric_cols = [c["column_name"] for c in self.schema if c["semantic_type"] == "numeric"]
            categorical_cols = [c["column_name"] for c in self.schema if c["semantic_type"] in ["categorical", "boolean"]]
            datetime_cols = [c["column_name"] for c in self.schema if c["semantic_type"] == "datetime"]
            
            # 1. Add Correlation Heatmap if we have multiple numeric cols
            if len(numeric_cols) >= 2:
                heatmap = self._compile_heatmap()
                if heatmap:
                    recommended_charts.append(heatmap)
                    
            # 2. Add Line Charts for Datetime + Numeric pairs
            if datetime_cols and numeric_cols:
                date_col = datetime_cols[0]  # take first datetime column
                for num_col in numeric_cols[:2]:  # limit to top 2 line charts
                    line_chart = self._compile_line_chart(date_col, num_col)
                    if line_chart:
                        recommended_charts.append(line_chart)
                        
            # 3. Add Histograms for Numeric columns
            for num_col in numeric_cols[:3]:  # limit to top 3 histograms
                hist = self._compile_histogram(num_col)
                if hist:
                    recommended_charts.append(hist)
                    
            # 4. Add Bar Charts for Categorical columns
            for cat_col in categorical_cols[:3]:  # limit to top 3 bar charts
                bar = self._compile_bar_chart(cat_col)
                if bar:
                    recommended_charts.append(bar)
                    
            # 5. Add Scatter Plots for Strongly Correlated numeric pairs
            strong_corrs = self.eda.get("correlations", {}).get("strong_correlations", [])
            scatter_count = 0
            for corr in strong_corrs:
                if scatter_count >= 2:
                    break
                scatter = self._compile_scatter_plot(corr["var1"], corr["var2"])
                if scatter:
                    recommended_charts.append(scatter)
                    scatter_count += 1
                    
            logger.info("visualization_agent_success", count=len(recommended_charts))
            return {
                "status": "success",
                "recommended_charts": recommended_charts
            }
            
        except Exception as e:
            logger.error("visualization_agent_failed", error=str(e))
            return {"status": "failed", "reason": str(e)}
