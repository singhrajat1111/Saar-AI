import os
import json
import requests
import structlog
from typing import Dict, Any, List
from app.core.reliability_helper import ReliabilityHelper

logger = structlog.get_logger()

class LLMAgent:
    """
    Agent responsible for generating narrative business insights, summary notes,
    risks, and opportunities from statistical analysis.
    Supports a dual-mode engine:
      - Rule-Based Mode: Runs Python statistical rules on EDA data. (Fallback / default)
      - LLM Mode: Connects via REST to Gemini/OpenAI to generate natural language narratives.
    """
    
    def __init__(self, schema_data: Dict[str, Any], eda_data: Dict[str, Any], ml_data: Dict[str, Any]):
        self.schema = schema_data.get("schema", []) if isinstance(schema_data, dict) else schema_data
        self.eda = eda_data
        self.ml = ml_data

    def _calculate_quality_score(self) -> Dict[str, Any]:
        """
        Computes a mathematical Data Quality Score (0 to 100) based on dataset imperfections.
        Also returns granular components: structure, completeness, consistency, reliability, readiness.
        """
        score = 100
        reasons = []
        
        quality = self.eda.get("quality", {})
        total_rows = quality.get("total_rows", 1)
        
        # 1. Missing values
        missing_vals = quality.get("missing_values", {})
        total_missing = sum(missing_vals.values()) if isinstance(missing_vals, dict) else 0
        missing_pct = (total_missing / (total_rows * len(self.schema))) * 100 if len(self.schema) > 0 and total_rows > 0 else 0
        
        if missing_pct > 0:
            deduction = min(25, missing_pct * 0.5)
            score -= deduction
            reasons.append(f"Deducted {round(deduction, 1)} points due to {round(missing_pct, 1)}% total missingness in the dataset.")
            
        # 2. Duplicate rows
        duplicates = quality.get("duplicate_rows", 0)
        dup_pct = (duplicates / total_rows) * 100 if total_rows > 0 else 0
        if duplicates > 0:
            deduction = min(15, 3 + dup_pct * 0.5)
            score -= deduction
            reasons.append(f"Deducted {round(deduction, 1)} points due to {duplicates} duplicate records ({round(dup_pct, 1)}%).")
            
        # 3. Empty columns
        empty_cols = quality.get("empty_columns", [])
        if empty_cols:
            deduction = min(20, len(empty_cols) * 8)
            score -= deduction
            reasons.append(f"Deducted {deduction} points due to empty columns: {', '.join(empty_cols)}.")
            
        # 4. Constant columns
        constant_cols = quality.get("constant_columns", [])
        # Exclude empty columns from constant count
        true_constant_cols = [c for c in constant_cols if c not in empty_cols]
        if true_constant_cols:
            deduction = min(15, len(true_constant_cols) * 4)
            score -= deduction
            reasons.append(f"Deducted {deduction} points due to constant columns offering zero variance: {', '.join(true_constant_cols)}.")
 
        # 5. Outliers
        numeric_stats = self.eda.get("numeric_stats", {})
        total_outliers = sum(s.get("outliers_count", 0) for s in numeric_stats.values())
        outlier_pct = (total_outliers / total_rows) * 100 if total_rows > 0 else 0
        if total_outliers > 0:
            deduction = min(10, outlier_pct * 0.2)
            score -= deduction
            reasons.append(f"Deducted {round(deduction, 1)} points due to presence of {total_outliers} numerical outliers.")

        # 6. Multicollinearity
        warnings = self.eda.get("correlations", {}).get("multicollinearity_warnings", [])
        if warnings:
            deduction = min(10, len(warnings) * 2)
            score -= deduction
            reasons.append(f"Deducted {deduction} points due to {len(warnings)} highly collinear feature pairs.")

        score = max(10, int(score))
        
        # Centralized reliability assessment
        assessment = ReliabilityHelper.assess(total_rows)
        if assessment.level == "UNRELIABLE":
            score = min(score, 70)
            reasons.append("Usability constraint: meaningful statistical inference cannot be performed on a single observation.")
            explanation = assessment.explanation
        elif assessment.level == "VERY_LIMITED":
            score = min(score, 75)
            reasons.append("Usability constraint: very limited statistical usability due to extremely small sample size.")
            explanation = assessment.explanation
        elif assessment.level == "LIMITED":
            score = min(score, 85)
            reasons.append("Usability constraint: limited statistical confidence due to small sample size.")
            explanation = assessment.explanation
        else:
            # Compile explanation
            if score >= 90:
                explanation = "Excellent data quality. The dataset is clean, complete, and contains minimal noise, duplicates, or missing fields."
            elif score >= 75:
                explanation = "Good data quality. Suitable for analysis, but contains minor missing values or outliers requiring imputation or scaling."
            elif score >= 50:
                explanation = "Moderate data quality. Contains significant duplicates, missing data points, or redundant columns. Review cleaning recommendations before modeling."
            else:
                explanation = "Poor data quality. High percentage of missing values, empty fields, or redundant records. Severe data preparation is required."

        # Compute granular quality score components
        # Structure component
        structure_deductions = (len(empty_cols) * 8) + (len(true_constant_cols) * 4)
        # Check for long column names
        long_names = sum(1 for col_info in self.schema if len(col_info.get("column_name", "")) > 100)
        structure_deductions += long_names * 5
        structure_score = max(10, 100 - structure_deductions)

        # Completeness component
        completeness_deductions = (missing_pct * 1.5) + (dup_pct * 1.0)
        completeness_score = max(10, 100 - completeness_deductions)

        # Consistency component
        consistency_deductions = (outlier_pct * 1.0) + (len(warnings) * 4)
        consistency_score = max(10, 100 - consistency_deductions)

        # Reliability component
        reliability_map = {
            "STANDARD": 100,
            "LIMITED": 85,
            "VERY_LIMITED": 60,
            "UNRELIABLE": 40
        }
        reliability_score = reliability_map.get(assessment.level, 100)

        # Readiness component
        readiness_map = {
            "STANDARD": 100,
            "LIMITED": 80,
            "VERY_LIMITED": 30,
            "UNRELIABLE": 10
        }
        readiness_score = readiness_map.get(assessment.level, 100)

        components = {
            "structure": int(structure_score),
            "completeness": int(completeness_score),
            "consistency": int(consistency_score),
            "reliability": int(reliability_score),
            "readiness": int(readiness_score)
        }

        return {
            "score": score,
            "explanation": explanation,
            "reasons": reasons,
            "components": components
        }

    def generate_rule_based_insights(self) -> Dict[str, Any]:
        """
        Generates highly grounded statistical and business insights using Python rules.
        """
        quality_info = self._calculate_quality_score()
        score = quality_info["score"]
        
        quality = self.eda.get("quality", {})
        total_rows = quality.get("total_rows", 0)
        num_cols = len(self.schema)
        
        assessment = ReliabilityHelper.assess(total_rows)

        # 1. Executive Summary
        if assessment.level == "UNRELIABLE":
            summary = (
                f"The dataset contains a single observation with {num_cols} attributes. "
                "Structural analysis was completed successfully, but meaningful statistical inference "
                "cannot be performed because additional observations are required. "
                f"The data quality/structure score is {score}/100."
            )
        elif assessment.level == "VERY_LIMITED":
            summary = (
                f"The dataset contains {total_rows} records and {num_cols} attributes. "
                "Structural analysis was completed successfully, but statistical reliability is very "
                f"limited due to the extremely small sample size. The data quality/structure score is {score}/100."
            )
        elif assessment.level == "LIMITED":
            summary = (
                f"The dataset contains {total_rows} records and {num_cols} attributes. "
                "Structural analysis was completed successfully, but statistical confidence is "
                f"limited due to the small sample size. The data quality/structure score is {score}/100."
            )
        else:
            summary = (
                f"The dataset contains {total_rows} records and {num_cols} attributes. "
                f"A comprehensive data quality evaluation yielded a score of {score}/100, indicating "
                f"{quality_info['explanation'].lower()} "
            )
            
            missing_vals = quality.get("missing_values", {})
            total_missing = sum(missing_vals.values()) if isinstance(missing_vals, dict) else 0
            if total_missing > 0:
                summary += f"A total of {total_missing} cells are missing values. "
                
            duplicates = quality.get("duplicate_rows", 0)
            if duplicates > 0:
                summary += f"There are {duplicates} duplicate rows detected. "
            
        # 2. Key Findings
        key_findings = []
        
        if assessment.level == "UNRELIABLE":
            key_findings = [
                "Dataset structure was successfully analyzed.",
                "Too few observations to infer statistical relationships.",
                "Distribution analysis is not meaningful with one observation.",
                "Additional data is required for reliable insights."
            ]
        elif assessment.level == "VERY_LIMITED":
            key_findings = [
                "Dataset structure was successfully analyzed.",
                "Very limited statistical sample size (2-4 rows). Inference may be highly unstable.",
                "Statistical distribution analysis has very low statistical power.",
                "Additional data collection is strongly recommended."
            ]
        else:
            # Missing values findings
            missing_percentages = quality.get("missing_percentages", {})
            high_missing = {col: pct for col, pct in missing_percentages.items() if pct > 10}
            for col, pct in high_missing.items():
                key_findings.append(
                    f"High missingness in '{col}': {round(pct, 1)}% of values are missing. "
                    "This requires imputation or exclusion to avoid biased estimates."
                )
                
            # Strong correlations findings
            strong_corrs = self.eda.get("correlations", {}).get("strong_correlations", [])
            for corr in strong_corrs[:4]:  # limit to top 4
                sig_text = "statistically significant" if corr["significant"] else "non-significant"
                key_findings.append(
                    f"Strong correlation between '{corr['var1']}' and '{corr['var2']}' "
                    f"(r = {corr['coefficient']}, p-value = {corr['p_value']}, {sig_text})."
                )
                
            # Multicollinearity warnings
            warnings = self.eda.get("correlations", {}).get("multicollinearity_warnings", [])
            for w in warnings[:3]:
                key_findings.append(
                    f"High multicollinearity warning: '{w['column']}' and '{w['correlated_with']}' "
                    f"exhibit a correlation coefficient of {w['coefficient']}. Consider dropping one during feature selection."
                )
                
            # Outlier findings
            numeric_stats = self.eda.get("numeric_stats", {})
            for col, stats_info in numeric_stats.items():
                out_pct = stats_info.get("outliers_pct", 0)
                if out_pct > 5:
                    key_findings.append(
                        f"Outliers detected in '{col}': {stats_info['outliers_count']} values ({out_pct}%) "
                        f"lie outside the 1.5x IQR boundary. Standard deviation is {round(stats_info['std'], 2)}."
                    )
                    
            # Normality tests findings
            for col, stats_info in numeric_stats.items():
                is_norm = stats_info.get("normality", {}).get("is_normal", True)
                if not is_norm:
                    skew = stats_info.get("skewness", 0)
                    kurt = stats_info.get("kurtosis", 0)
                    key_findings.append(
                        f"Non-normal distribution in '{col}': The column shows a skewness of {round(skew, 2)} "
                        f"and kurtosis of {round(kurt, 2)}, deviating significantly from normality (p < 0.05)."
                    )

            # Hypothesis test findings
            hyp_tests = self.eda.get("hypothesis_tests", [])
            for test in hyp_tests:
                if test.get("significant"):
                    key_findings.append(
                        f"Hypothesis Test Result ({test['test_type']}): {test['interpretation']}"
                    )
                    
            # Default findings if empty
            if not key_findings:
                if assessment.level == "LIMITED":
                    key_findings = [
                        "Dataset structure was successfully analyzed, but confidence is limited due to the small sample size.",
                        "Statistical correlations and distribution shapes are exploratory and should not be used for critical inferences."
                    ]
                else:
                    key_findings.append("No unusual statistical anomalies, strong correlations, or significant relationships were found in the dataset.")
                    key_findings.append("Data distributions are generally symmetrical and free from extreme multicollinearity or duplicate records.")
            
        # 3. Risks & Opportunities
        risks = []
        opportunities = []
        
        if assessment.requires_caution():
            for w in assessment.warnings:
                risks.append(w)
            for action in assessment.recommended_actions:
                risks.append(f"Recommended Action: {action}")
        else:
            total_missing = sum(quality.get("missing_values", {}).values()) if isinstance(quality.get("missing_values"), dict) else 0
            if total_missing > 0:
                risks.append("Missing values present a risk of bias if ignored or removed in a naive manner (e.g. listwise deletion).")
            if duplicates > 0:
                risks.append("Duplicate rows are present, which could cause double-counting and artificially shrink standard errors during modeling.")
            warnings = self.eda.get("correlations", {}).get("multicollinearity_warnings", [])
            if len(warnings) > 0:
                risks.append("High multicollinearity will increase the variance of regression coefficients, making model interpretation unstable.")
            numeric_stats = self.eda.get("numeric_stats", {})
            if any(s.get("outliers_pct", 0) > 8 for s in numeric_stats.values()):
                risks.append("Heavy outlier distributions might excessively influence model training, skewing predictions for standard inputs.")
                
            if not risks:
                risks.append("No high-severity statistical risks detected. The dataset structure is robust.")
            
        # Opportunities
        if assessment.level == "UNRELIABLE":
            opportunities = ["Collect additional observations to discover meaningful statistical relationships and patterns."]
        elif assessment.level == "VERY_LIMITED":
            opportunities = ["Collect more data to increase statistical power and unlock predictive modeling opportunities."]
        else:
            strong_corrs = self.eda.get("correlations", {}).get("strong_correlations", [])
            if len(strong_corrs) > 0:
                opportunities.append("Leverage strongly correlated feature groups for dimensional reduction (e.g. PCA) or predictive model building.")
            
            hyp_tests = self.eda.get("hypothesis_tests", [])
            sig_tests = [t for t in hyp_tests if t.get("significant")]
            if sig_tests:
                opportunities.append(f"Statistically significant associations detected (e.g., {sig_tests[0]['test_name']}). These represent high-impact business target segmentation opportunities.")
                
            numeric_stats = self.eda.get("numeric_stats", {})
            if len(numeric_stats) >= 2:
                opportunities.append("The presence of multiple numeric features enables multivariate clustering algorithms to segment the dataset dynamically.")
                
            if not opportunities:
                opportunities.append("Consider collecting additional attributes to uncover hidden correlations or multivariate patterns.")

        return {
            "status": "success",
            "executive_summary": summary,
            "key_findings": key_findings[:8],  # limit to top 8 findings
            "risks": risks,
            "opportunities": opportunities,
            "quality_score": score,
            "quality_score_components": quality_info["components"],
            "quality_score_explanation": quality_info["explanation"],
            "quality_score_reasons": quality_info["reasons"],
            "confidence_score": round(max(0.1, score / 100), 2)
        }

    def execute(self) -> Dict[str, Any]:
        logger.info("llm_agent_start")
        
        # 1. Compute high-quality Python rule-based insights first (Ground Truth)
        rules_insights = self.generate_rule_based_insights()
        
        # 2. Check if API keys are set for narrative enhancement
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if not gemini_key and not openai_key:
            logger.info("llm_agent_rule_mode", reason="No API keys present. Using local rule-based engine.")
            return rules_insights
            
        # Format the context for LLM
        context = {
            "schema_overview": self.schema,
            "quality_overview": self.eda.get("quality", {}),
            "descriptive_statistics": self.eda.get("numeric_stats", {}),
            "correlations": self.eda.get("correlations", {}),
            "hypothesis_tests": self.eda.get("hypothesis_tests", []),
            "ml_recommendations": self.ml.get("potential_targets", []),
            "rule_based_insights_draft": rules_insights
        }
        
        system_prompt = """
You are SAAR AI, a world-class, professional Data Analyst and Consultant.
Your task is to take the provided statistical context and draft a beautiful, professional, narrative analysis report.
The report must include:
- An Executive Summary (highly descriptive, professional, highlighting the business implications).
- Key Findings (list of bulleted narrative points detailing patterns, statistics, correlations, or anomalies).
- Business Risks (statistical issues or bad patterns that could harm business decisions).
- Business Opportunities (areas where the data shows potential for growth, modeling, or optimization).

Your response MUST be strict JSON in this format:
{
  "executive_summary": "...",
  "key_findings": ["...", "..."],
  "risks": ["...", "..."],
  "opportunities": ["...", "..."]
}
Every insight must match the mathematical reality in the context. Do not make up any numbers or columns. Keep the tone professional, precise, and executive-ready.
"""

        # Try Gemini API if key is present
        if gemini_key:
            try:
                logger.info("llm_agent_calling_gemini")
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
                headers = {"Content-Type": "application/json"}
                payload = {
                    "contents": [
                        {
                            "parts": [
                                {"text": f"{system_prompt}\n\nContext Data JSON:\n{json.dumps(context)}"}
                            ]
                        }
                    ],
                    "generationConfig": {
                        "responseMimeType": "application/json"
                    }
                }
                
                response = requests.post(url, headers=headers, json=payload, timeout=15)
                if response.status_code == 200:
                    resp_json = response.json()
                    # Extract the JSON text content
                    text_content = resp_json["candidates"][0]["content"]["parts"][0]["text"]
                    cleaned_content = json.loads(text_content.strip())
                    
                    # Merge quality score from rule-based calculation
                    rules_insights["executive_summary"] = cleaned_content.get("executive_summary", rules_insights["executive_summary"])
                    rules_insights["key_findings"] = cleaned_content.get("key_findings", rules_insights["key_findings"])
                    rules_insights["risks"] = cleaned_content.get("risks", rules_insights["risks"])
                    rules_insights["opportunities"] = cleaned_content.get("opportunities", rules_insights["opportunities"])
                    
                    logger.info("llm_agent_gemini_success")
                    return rules_insights
                else:
                    logger.warn("gemini_api_returned_error", status_code=response.status_code, body=response.text)
            except Exception as e:
                logger.error("gemini_call_failed", error=str(e))
                
        # Try OpenAI API if key is present
        elif openai_key:
            try:
                logger.info("llm_agent_calling_openai")
                url = "https://api.openai.com/v1/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {openai_key}"
                }
                payload = {
                    "model": "gpt-4o-mini",
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Context Data JSON:\n{json.dumps(context)}"}
                    ]
                }
                response = requests.post(url, headers=headers, json=payload, timeout=15)
                if response.status_code == 200:
                    resp_json = response.json()
                    text_content = resp_json["choices"][0]["message"]["content"]
                    cleaned_content = json.loads(text_content.strip())
                    
                    # Merge quality score from rule-based calculation
                    rules_insights["executive_summary"] = cleaned_content.get("executive_summary", rules_insights["executive_summary"])
                    rules_insights["key_findings"] = cleaned_content.get("key_findings", rules_insights["key_findings"])
                    rules_insights["risks"] = cleaned_content.get("risks", rules_insights["risks"])
                    rules_insights["opportunities"] = cleaned_content.get("opportunities", rules_insights["opportunities"])
                    
                    logger.info("llm_agent_openai_success")
                    return rules_insights
                else:
                    logger.warn("openai_api_returned_error", status_code=response.status_code, body=response.text)
            except Exception as e:
                logger.error("openai_call_failed", error=str(e))

        # Fallback if both failed or not set
        logger.info("llm_agent_fallback_to_rules")
        return rules_insights
