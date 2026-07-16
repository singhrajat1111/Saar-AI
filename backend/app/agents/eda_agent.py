import pandas as pd
import numpy as np
import scipy.stats as stats
import structlog
from typing import Dict, Any, List

logger = structlog.get_logger()

def make_serializable(val):
    if pd.isna(val):
        return None
    if isinstance(val, (np.integer, np.int64, np.int32, np.int16, np.byte)):
        return int(val)
    if isinstance(val, (np.floating, np.float64, np.float32, np.float16)):
        if np.isnan(val) or np.isinf(val):
            return None
        return float(val)
    if isinstance(val, (np.bool_)):
        return bool(val)
    if isinstance(val, np.ndarray):
        return [make_serializable(x) for x in val]
    return val

def sanitize_data(data):
    if isinstance(data, dict):
        return {k: sanitize_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_data(v) for v in data]
    else:
        return make_serializable(data)

class EDAAgent:
    """
    Agent responsible for Exploratory Data Analysis (EDA) and rigorous statistical profiling.
    Computes summary stats, skewness, kurtosis, percentiles, outlier limits,
    correlation matrices with p-values, multicollinearity alerts,
    and runs hypothesis tests (Normality, T-Test, ANOVA, Chi-Square).
    """
    
    def __init__(self, dataframe: pd.DataFrame):
        self.df = dataframe

    def execute(self) -> Dict[str, Any]:
        logger.info("eda_agent_start", rows=len(self.df), cols=len(self.df.columns))
        
        try:
            # 1. Quality summary
            missing_vals = self.df.isnull().sum().to_dict()
            missing_pct = (self.df.isnull().sum() / len(self.df) * 100).to_dict() if len(self.df) > 0 else {col: 0.0 for col in self.df.columns}
            duplicates = int(self.df.duplicated().sum()) if len(self.df) > 0 else 0
            memory_usage = int(self.df.memory_usage(deep=True).sum())
            
            # Detect constant, empty, and high-cardinality columns
            empty_cols = [col for col, count in missing_vals.items() if count == len(self.df)] if len(self.df) > 0 else []
            constant_cols = [col for col in self.df.columns if self.df[col].nunique() == 1]
            
            # Separate numeric and categorical columns
            numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
            # Exclude identifiers and text from standard categorical stats if needed,
            # but we can do it for all non-numeric columns.
            categorical_cols = self.df.select_dtypes(exclude=[np.number]).columns.tolist()
            
            numeric_stats = {}
            categorical_stats = {}
            
            # 2. Detailed Numerical Stats
            for col in numeric_cols:
                series = self.df[col].dropna()
                if series.empty:
                    continue
                    
                # Descriptive metrics
                mean_val = series.mean()
                median_val = series.median()
                mode_series = series.mode()
                mode_val = mode_series.iloc[0] if not mode_series.empty else None
                var_val = series.var()
                std_val = series.std()
                min_val = series.min()
                max_val = series.max()
                
                # Skewness & Kurtosis
                try:
                    skew_val = float(stats.skew(series)) if len(series) >= 3 else 0.0
                    if np.isnan(skew_val) or np.isinf(skew_val):
                        skew_val = 0.0
                except Exception:
                    skew_val = 0.0

                try:
                    kurt_val = float(stats.kurtosis(series)) if len(series) >= 3 else 0.0
                    if np.isnan(kurt_val) or np.isinf(kurt_val):
                        kurt_val = 0.0
                except Exception:
                    kurt_val = 0.0
                
                # Percentiles
                q25 = series.quantile(0.25)
                q50 = series.quantile(0.50)
                q75 = series.quantile(0.75)
                p5 = series.quantile(0.05)
                p95 = series.quantile(0.95)
                
                # Outlier detection (IQR)
                iqr = q75 - q25
                lower_bound = q25 - 1.5 * iqr
                upper_bound = q75 + 1.5 * iqr
                outliers = series[(series < lower_bound) | (series > upper_bound)]
                outliers_count = len(outliers)
                outliers_pct = (outliers_count / len(series)) * 100 if len(series) > 0 else 0.0
                
                # Normality Test (Shapiro-Wilk for N <= 5000, D'Agostino for N > 5000)
                norm_stat, norm_p = 0.0, 1.0
                is_normal = True
                if len(series) >= 8:
                    try:
                        if len(series) <= 5000:
                            norm_stat, norm_p = stats.shapiro(series)
                        else:
                            norm_stat, norm_p = stats.normaltest(series)
                        is_normal = bool(norm_p >= 0.05)
                    except Exception:
                        pass
                
                numeric_stats[col] = {
                    "mean": mean_val,
                    "median": median_val,
                    "mode": mode_val,
                    "variance": var_val,
                    "std": std_val,
                    "min": min_val,
                    "max": max_val,
                    "skewness": skew_val,
                    "kurtosis": kurt_val,
                    "q25": q25,
                    "q50": q50,
                    "q75": q75,
                    "p5": p5,
                    "p95": p95,
                    "outliers_count": outliers_count,
                    "outliers_pct": round(outliers_pct, 2),
                    "normality": {
                        "stat": norm_stat,
                        "p_value": norm_p,
                        "is_normal": is_normal
                    }
                }
                
            # 3. Detailed Categorical Stats
            for col in categorical_cols:
                series = self.df[col].dropna()
                n_unique = series.nunique()
                
                # Top value distributions
                value_counts = series.value_counts().head(10)
                top_categories = []
                for val, count in value_counts.items():
                    pct_val = round(float(count / len(self.df) * 100), 2) if len(self.df) > 0 else 0.0
                    top_categories.append({
                        "value": str(val),
                        "count": int(count),
                        "percentage": pct_val
                    })
                    
                categorical_stats[col] = {
                    "unique_count": n_unique,
                    "top_categories": top_categories
                }

            # 4. Correlation Analysis
            correlations_matrix = {}
            strong_correlations = []
            multicollinearity_warnings = []
            
            # Filter numerical columns for correlation with variance > 0
            def is_valid_variance(v):
                if v is None or pd.isna(v):
                    return False
                try:
                    return float(v) > 0
                except Exception:
                    return False
            valid_corr_cols = [col for col in numeric_cols if col in numeric_stats and is_valid_variance(numeric_stats[col].get("variance"))]
            
            if len(valid_corr_cols) >= 2:
                corr_matrix = self.df[valid_corr_cols].corr()
                if hasattr(corr_matrix, 'round'):
                    corr_df = corr_matrix.round(3)
                else:
                    corr_df = round(corr_matrix, 3)
                
                if hasattr(corr_df, 'columns'):
                    for col in corr_df.columns:
                        correlations_matrix[col] = corr_df[col].to_dict()
                elif hasattr(corr_df, 'to_dict'):
                    correlations_matrix = corr_df.to_dict()
                else:
                    logger.warning("unexpected_corr_matrix_type", corr_type=type(corr_df))
                    
                # Pairwise significance and warnings
                for i in range(len(valid_corr_cols)):
                    for j in range(i + 1, len(valid_corr_cols)):
                        col1 = valid_corr_cols[i]
                        col2 = valid_corr_cols[j]
                        
                        # Compute correlation p-value
                        series1 = self.df[col1].fillna(self.df[col1].median())
                        series2 = self.df[col2].fillna(self.df[col2].median())
                        
                        try:
                            coef, p_val = stats.pearsonr(series1, series2)
                            coef = round(coef, 3)
                            p_val = round(p_val, 4)
                            
                            # Filter Strong Correlation
                            if abs(coef) >= 0.7:
                                strong_correlations.append({
                                    "var1": col1,
                                    "var2": col2,
                                    "coefficient": coef,
                                    "p_value": p_val,
                                    "significant": bool(p_val < 0.05)
                                })
                                
                            # Multicollinearity Check
                            if abs(coef) >= 0.8:
                                multicollinearity_warnings.append({
                                    "column": col1,
                                    "correlated_with": col2,
                                    "coefficient": coef
                                })
                        except Exception:
                            pass

            # 5. Automated Hypothesis Testing
            hypothesis_tests = []
            
            # Limit tests to keep the JSON payloads and reports highly focused
            t_test_count = 0
            anova_count = 0
            chi_square_count = 0
            
            # Independent T-Test (Binary Categorical vs Numerical)
            for cat_col in categorical_cols:
                if t_test_count >= 5:
                    break
                cat_series = self.df[cat_col].dropna()
                unique_vals = cat_series.unique()
                if len(unique_vals) != 2:
                    continue
                    
                val1, val2 = unique_vals[0], unique_vals[1]
                
                for num_col in numeric_cols:
                    if t_test_count >= 5:
                        break
                    group1 = self.df[self.df[cat_col] == val1][num_col].dropna()
                    group2 = self.df[self.df[cat_col] == val2][num_col].dropna()
                    
                    if len(group1) >= 5 and len(group2) >= 5:
                        try:
                            t_stat, p_val = stats.ttest_ind(group1, group2, equal_var=False)
                            significant = p_val < 0.05
                            hypothesis_tests.append({
                                "test_type": "T-Test",
                                "test_name": f"Independent Two-Sample T-Test ({cat_col} vs {num_col})",
                                "variables": [cat_col, num_col],
                                "statistic": float(t_stat),
                                "p_value": float(p_val),
                                "significant": bool(significant),
                                "interpretation": f"The mean of '{num_col}' is significantly different between groups '{val1}' and '{val2}' (p < 0.05)." if significant else f"No statistically significant difference in the mean of '{num_col}' between groups '{val1}' and '{val2}'."
                            })
                            t_test_count += 1
                        except Exception:
                            pass

            # One-Way ANOVA (Categorical (>2 groups) vs Numerical)
            for cat_col in categorical_cols:
                if anova_count >= 5:
                    break
                cat_series = self.df[cat_col].dropna()
                unique_vals = cat_series.unique()
                # ANOVA is suitable for 3 to 10 unique groups
                if len(unique_vals) < 3 or len(unique_vals) > 10:
                    continue
                    
                for num_col in numeric_cols:
                    if anova_count >= 5:
                        break
                    groups = [self.df[self.df[cat_col] == val][num_col].dropna() for val in unique_vals]
                    # Filter out empty or extremely small groups
                    groups = [g for g in groups if len(g) >= 5]
                    
                    if len(groups) >= 3:
                        try:
                            f_stat, p_val = stats.f_oneway(*groups)
                            significant = p_val < 0.05
                            hypothesis_tests.append({
                                "test_type": "ANOVA",
                                "test_name": f"One-Way ANOVA ({cat_col} vs {num_col})",
                                "variables": [cat_col, num_col],
                                "statistic": float(f_stat),
                                "p_value": float(p_val),
                                "significant": bool(significant),
                                "interpretation": f"There are statistically significant differences between the group means of '{num_col}' across categories of '{cat_col}' (p < 0.05)." if significant else f"No significant differences were found between the group means of '{num_col}' across categories of '{cat_col}'."
                            })
                            anova_count += 1
                        except Exception:
                            pass

            # Chi-Square Test (Categorical vs Categorical)
            for i in range(len(categorical_cols)):
                if chi_square_count >= 5:
                    break
                for j in range(i + 1, len(categorical_cols)):
                    if chi_square_count >= 5:
                        break
                    cat1 = categorical_cols[i]
                    cat2 = categorical_cols[j]
                    
                    # Ensure reasonable group sizes (2 to 10 unique values)
                    if not (2 <= self.df[cat1].nunique() <= 10) or not (2 <= self.df[cat2].nunique() <= 10):
                        continue
                        
                    try:
                        contingency_table = pd.crosstab(self.df[cat1], self.df[cat2])
                        chi2, p_val, dof, expected = stats.chi2_contingency(contingency_table)
                        significant = p_val < 0.05
                        hypothesis_tests.append({
                            "test_type": "Chi-Square",
                            "test_name": f"Chi-Square Test of Independence ({cat1} vs {cat2})",
                            "variables": [cat1, cat2],
                            "statistic": float(chi2),
                            "p_value": float(p_val),
                            "significant": bool(significant),
                            "interpretation": f"There is a statistically significant association between '{cat1}' and '{cat2}' (p < 0.05)." if significant else f"No significant association was detected between '{cat1}' and '{cat2}' (independent)."
                        })
                        chi_square_count += 1
                    except Exception:
                        pass

            # Create the final result dict
            eda_result = {
                "status": "success",
                "quality": {
                    "total_rows": len(self.df),
                    "missing_values": missing_vals,
                    "missing_percentages": missing_pct,
                    "duplicate_rows": duplicates,
                    "memory_usage_bytes": memory_usage,
                    "empty_columns": empty_cols,
                    "constant_columns": constant_cols
                },
                "numeric_stats": numeric_stats,
                "categorical_stats": categorical_stats,
                "correlations": {
                    "matrix": correlations_matrix,
                    "strong_correlations": strong_correlations,
                    "multicollinearity_warnings": multicollinearity_warnings
                },
                "hypothesis_tests": hypothesis_tests
            }

            # Return recursively sanitized dict to ensure JSON compliance
            return sanitize_data(eda_result)
            
        except Exception as e:
            logger.error("eda_agent_error", error=str(e))
            return {"status": "failed", "reason": str(e)}
