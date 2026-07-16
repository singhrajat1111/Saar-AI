"""
data_compiler.py
────────────────
Central data extraction layer for the Export Center.
Reads from the DatasetStore registry and organises everything into a flat
ReportData dataclass. NO new analysis is performed here.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.core.reliability_helper import ReliabilityHelper

SAAR_VERSION = "1.0"
METHODOLOGY = (
    "This report was generated using deterministic statistical analysis performed by "
    "SAAR's Python Statistical Engine. Natural language explanations may have been enhanced "
    "using AI. AI did not calculate, modify, or invent any statistical values."
)


@dataclass
class ColumnProfile:
    name: str
    semantic_type: str
    pandas_type: str
    null_count: int
    null_pct: float
    unique_count: int
    stats_summary: str      # human-readable, e.g. "Mean: 29.7 | Median: 28.0"
    outlier_count: int
    outlier_pct: float
    top_categories: List[Dict]   # [{value, count, percentage}] for categoricals
    histogram: List[float]       # simplified bucketed values for bar chart


@dataclass
class HypothesisTest:
    test_name: str
    test_type: str
    variables: List[str]
    statistic: Optional[float]
    p_value: Optional[float]
    significant: bool
    interpretation: str


@dataclass
class ReportData:
    # ── Metadata ─────────────────────────────────────────────────────────────
    filename: str
    base_name: str          # filename without extension
    rows: int
    columns: int
    missing_total: int
    duplicates: int
    generated_at: str       # ISO timestamp
    generated_at_display: str  # human-readable
    report_type: str        # "technical" | "executive"
    saar_version: str = SAAR_VERSION

    # ── Quality ───────────────────────────────────────────────────────────────
    quality_score: int = 100
    quality_explanation: str = ""
    quality_reasons: List[str] = field(default_factory=list)
    quality_score_components: Dict[str, int] = field(default_factory=dict)

    # ── AI Insights ───────────────────────────────────────────────────────────
    executive_summary: str = ""
    key_findings: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)

    # ── Column profiles ───────────────────────────────────────────────────────
    column_profiles: List[ColumnProfile] = field(default_factory=list)

    # ── Statistical tests ─────────────────────────────────────────────────────
    hypothesis_tests: List[HypothesisTest] = field(default_factory=list)

    # ── Cleaning history ──────────────────────────────────────────────────────
    cleaning_history: List[Dict] = field(default_factory=list)

    # ── ML recommendations ────────────────────────────────────────────────────
    potential_targets: List[Dict] = field(default_factory=list)
    unsupervised_recs: List[Dict] = field(default_factory=list)

    # ── File info ─────────────────────────────────────────────────────────────
    file_format: str = ""

    # ── Methodology ───────────────────────────────────────────────────────────
    methodology: str = METHODOLOGY

    # ── Reliability Assessment ────────────────────────────────────────────────
    has_statistical_limitations: bool = False
    reliability_level: str = "STANDARD"
    reliability_explanation: str = ""
    reliability_warnings: List[str] = field(default_factory=list)
    reliability_actions: List[str] = field(default_factory=list)
    is_reliable: bool = True
    can_model: bool = True


def _safe_float(v, decimals: int = 2) -> float:
    try:
        return round(float(v), decimals)
    except Exception:
        return 0.0


def _build_histogram(ns: Dict) -> List[float]:
    """Build a simplified 5-bucket histogram from numeric stats for bar charts."""
    try:
        mn = _safe_float(ns.get("min", 0))
        q1 = _safe_float(ns.get("q1", 0))
        median = _safe_float(ns.get("median", 0))
        q3 = _safe_float(ns.get("q3", 0))
        mx = _safe_float(ns.get("max", 0))
        # Relative bucket widths for illustration
        return [mn, q1, median, q3, mx]
    except Exception:
        return [0, 0, 0, 0, 0]


def compile_report_data(dataset: Dict[str, Any], report_type: str = "technical") -> ReportData:
    """
    Compile all verified analysis results from the dataset registry into
    a flat ReportData object ready for rendering. No new analysis is performed.
    """
    now = datetime.now(timezone.utc)
    generated_at = now.isoformat()
    generated_at_display = now.strftime("%Y-%m-%d at %H:%M UTC")

    filename = dataset.get("filename", "Dataset")
    base_name = os.path.splitext(filename)[0]
    ai = dataset.get("ai_insights", {})
    eda = dataset.get("eda", {})
    schema = dataset.get("schema", [])
    num_stats = eda.get("numeric_stats", {})
    cat_stats = eda.get("categorical_stats", {})

    # ── Column profiles ───────────────────────────────────────────────────────
    profiles: List[ColumnProfile] = []
    for col in schema:
        cname = col.get("column_name", "")
        stype = col.get("semantic_type", "unknown")
        ptype = col.get("pandas_dtype", "")
        null_count = col.get("null_count", 0)
        null_pct = _safe_float(col.get("null_percentage", 0))
        unique_count = col.get("unique_values", 0)

        stats_summary = "N/A"
        outlier_count = 0
        outlier_pct = 0.0
        top_cats: List[Dict] = []
        histogram: List[float] = []

        if stype == "numeric" and cname in num_stats:
            ns = num_stats[cname]
            mean = _safe_float(ns.get("mean", 0))
            median = _safe_float(ns.get("median", 0))
            std = _safe_float(ns.get("std", 0))
            mn = _safe_float(ns.get("min", 0))
            mx = _safe_float(ns.get("max", 0))
            stats_summary = f"Mean: {mean} | Median: {median} | Std: {std} | Min: {mn} | Max: {mx}"
            outlier_count = int(ns.get("outliers_count", 0))
            outlier_pct = _safe_float(ns.get("outliers_pct", 0))
            histogram = _build_histogram(ns)

        elif stype in ("categorical", "boolean") and cname in cat_stats:
            cs = cat_stats[cname]
            top_cats = cs.get("top_categories", [])[:5]
            if top_cats:
                top = top_cats[0]
                stats_summary = f"Mode: '{top['value']}' ({top['percentage']}%)"

        profiles.append(ColumnProfile(
            name=cname, semantic_type=stype, pandas_type=ptype,
            null_count=null_count, null_pct=null_pct,
            unique_count=unique_count, stats_summary=stats_summary,
            outlier_count=outlier_count, outlier_pct=outlier_pct,
            top_categories=top_cats, histogram=histogram,
        ))

    # ── Hypothesis tests ──────────────────────────────────────────────────────
    tests: List[HypothesisTest] = []
    raw_tests = eda.get("hypothesis_tests", [])
    for t in raw_tests:
        tests.append(HypothesisTest(
            test_name=t.get("test_name", ""),
            test_type=t.get("test_type", ""),
            variables=t.get("variables", []),
            statistic=t.get("statistic"),
            p_value=t.get("p_value"),
            significant=t.get("significant", False),
            interpretation=t.get("interpretation", ""),
        ))

    # Add normality tests from numeric_stats
    for cname, ns in num_stats.items():
        norm = ns.get("normality")
        if norm:
            is_normal = norm.get("is_normal", True)
            tests.append(HypothesisTest(
                test_name=f"Shapiro-Wilk: '{cname}'",
                test_type="Normality Test",
                variables=[cname],
                statistic=_safe_float(norm.get("stat", 0), 4),
                p_value=_safe_float(norm.get("p_value", 1.0), 4),
                significant=not is_normal,
                interpretation=(
                    f"'{cname}' is {'not ' if not is_normal else ''}normally distributed "
                    f"(p {'< 0.05' if not is_normal else '>= 0.05'})."
                ),
            ))

    # ── ML recommendations ────────────────────────────────────────────────────
    ml = dataset.get("ml_recommendations", {})
    
    rows_count = dataset.get("rows_count", 0)
    assessment = ReliabilityHelper.assess(rows_count)

    return ReportData(
        filename=filename,
        base_name=base_name,
        rows=rows_count,
        columns=dataset.get("columns_count", 0),
        missing_total=dataset.get("missing_values_count", 0),
        duplicates=dataset.get("duplicates_count", 0),
        generated_at=generated_at,
        generated_at_display=generated_at_display,
        report_type=report_type,
        quality_score=int(ai.get("quality_score", 100)),
        quality_explanation=ai.get("quality_score_explanation", ""),
        quality_reasons=ai.get("quality_score_reasons", []),
        quality_score_components=ai.get("quality_score_components", {}),
        executive_summary=ai.get("executive_summary", "No executive summary available."),
        key_findings=ai.get("key_findings", []),
        risks=ai.get("risks", []),
        opportunities=ai.get("opportunities", []),
        column_profiles=profiles,
        hypothesis_tests=tests,
        cleaning_history=dataset.get("cleaning_history", []),
        potential_targets=ml.get("potential_targets", []),
        unsupervised_recs=ml.get("unsupervised_recommendations", []),
        file_format=dataset.get("format", ""),
        has_statistical_limitations=not assessment.is_reliable(),
        reliability_level=assessment.level,
        reliability_explanation=assessment.explanation,
        reliability_warnings=assessment.warnings,
        reliability_actions=assessment.recommended_actions,
        is_reliable=assessment.is_reliable(),
        can_model=assessment.can_model,
    )


def generate_filename(base_name: str, report_type: str, fmt: str, now: Optional[datetime] = None) -> str:
    """Generate a professional, collision-resistant filename."""
    if now is None:
        now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d_%H-%M")
    clean_base = base_name.replace(" ", "_").replace(",", "")
    rtype = report_type.title()  # "Technical" or "Executive"
    ext_map = {"html": "html", "pdf": "pdf", "markdown": "md", "json": "json"}
    ext = ext_map.get(fmt, fmt)
    if fmt == "json":
        return f"{clean_base}_Report_{date_str}.{ext}"
    return f"{clean_base}_{rtype}_Report_{date_str}.{ext}"
