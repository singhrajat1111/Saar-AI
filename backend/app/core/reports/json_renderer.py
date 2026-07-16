"""
json_renderer.py
────────────────
Generates structured JSON exports from ReportData.
Includes extended metadata for API integration.
"""
from __future__ import annotations

import json
from typing import Dict, Any
from app.core.reports.data_compiler import ReportData

def render_json(d: ReportData) -> str:
    """Render a structured JSON object containing all compiled statistics and metadata."""
    data = {
        "metadata": {
            "filename": d.filename,
            "rows": d.rows,
            "columns": d.columns,
            "generated_at": d.generated_at,
            "generated_by": "SAAR V1",
            "analysis_engine": "Python Statistical Engine",
            "ai_layer": "Optional Explanation Layer",
            "report_version": d.saar_version,
            "report_type": d.report_type
        },
        "quality": {
            "score": d.quality_score,
            "explanation": d.quality_explanation,
            "reasons": d.quality_reasons
        },
        "executive_summary": d.executive_summary,
        "key_findings": d.key_findings,
        "risks": d.risks,
        "opportunities": d.opportunities,
        "column_profiles": [
            {
                "name": p.name,
                "semantic_type": p.semantic_type,
                "pandas_type": p.pandas_type,
                "null_count": p.null_count,
                "null_pct": p.null_pct,
                "unique_count": p.unique_count,
                "stats_summary": p.stats_summary,
                "outlier_count": p.outlier_count,
                "outlier_pct": p.outlier_pct,
                "top_categories": p.top_categories,
                "histogram": p.histogram
            }
            for p in d.column_profiles
        ],
        "hypothesis_tests": [
            {
                "test_name": t.test_name,
                "test_type": t.test_type,
                "variables": t.variables,
                "statistic": t.statistic,
                "p_value": t.p_value,
                "significant": t.significant,
                "interpretation": t.interpretation
            }
            for t in d.hypothesis_tests
        ],
        "cleaning_history": d.cleaning_history,
        "ml_recommendations": {
            "potential_targets": d.potential_targets,
            "unsupervised_recommendations": d.unsupervised_recs
        },
        "methodology": d.methodology
    }
    return json.dumps(data, indent=2)
