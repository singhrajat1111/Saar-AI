"""
pdf_renderer.py
───────────────
Generates professional PDF reports from ReportData using ReportLab.
No external fonts. No system dependencies. Fully deterministic.
Two variants: Technical (full detail) and Executive (business summary).
"""
from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether,
)
from reportlab.platypus.flowables import Flowable
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics import renderPDF

from app.core.reports.data_compiler import ReportData

# ── Brand colours ──────────────────────────────────────────────────────────────
C_DARK   = HexColor("#1a1a2e")
C_BLUE   = HexColor("#0f3460")
C_ACCENT = HexColor("#1a73e8")
C_GREEN  = HexColor("#22c55e")
C_AMBER  = HexColor("#f59e0b")
C_RED    = HexColor("#ef4444")
C_GREY   = HexColor("#64748b")
C_LGREY  = HexColor("#f1f5f9")
C_BORDER = HexColor("#e2e8f0")
C_WHITE  = colors.white

W, H = A4   # 595.27 x 841.89 pt
MARGIN = 45 * mm
CONTENT_W = W - 2 * MARGIN


# ── Helpers ────────────────────────────────────────────────────────────────────

def _score_color(score: int) -> "HexColor":
    if score >= 80: return C_GREEN
    if score >= 60: return C_AMBER
    return C_RED


def _styles():
    base = getSampleStyleSheet()
    def s(name, **kw):
        return ParagraphStyle(name, parent=base["Normal"], **kw)
    return {
        "h1": s("H1", fontName="Helvetica-Bold", fontSize=22, textColor=C_DARK, spaceAfter=6),
        "h2": s("H2", fontName="Helvetica-Bold", fontSize=14, textColor=C_BLUE, spaceBefore=14, spaceAfter=6, borderPadding=(0,0,4,0)),
        "h3": s("H3", fontName="Helvetica-Bold", fontSize=11, textColor=C_DARK, spaceBefore=8, spaceAfter=4),
        "body": s("Body", fontName="Helvetica", fontSize=9.5, textColor=C_DARK, leading=14, spaceAfter=4),
        "small": s("Small", fontName="Helvetica", fontSize=8, textColor=C_GREY, leading=12),
        "caption": s("Caption", fontName="Helvetica-Oblique", fontSize=8, textColor=C_GREY, spaceAfter=6),
        "bullet": s("Bullet", fontName="Helvetica", fontSize=9.5, textColor=C_DARK, leading=14, leftIndent=12, spaceAfter=3),
        "center": s("Center", fontName="Helvetica", fontSize=9.5, alignment=TA_CENTER),
        "label": s("Label", fontName="Helvetica-Bold", fontSize=7.5, textColor=C_GREY, alignment=TA_CENTER),
        "methodology": s("Method", fontName="Helvetica-Oblique", fontSize=9, textColor=C_GREY, leading=14, spaceAfter=4),
        "cover_title": s("CoverTitle", fontName="Helvetica-Bold", fontSize=28, textColor=C_WHITE),
        "cover_sub": s("CoverSub", fontName="Helvetica", fontSize=13, textColor=HexColor("#aab4c4")),
        "cover_file": s("CoverFile", fontName="Helvetica-Bold", fontSize=16, textColor=C_WHITE),
        "cover_meta": s("CoverMeta", fontName="Helvetica", fontSize=10, textColor=HexColor("#aab4c4"), alignment=TA_CENTER),
        "cover_meta_val": s("CoverMetaVal", fontName="Helvetica-Bold", fontSize=13, textColor=C_WHITE, alignment=TA_CENTER),
    }


# ── Page template (header + footer) ───────────────────────────────────────────

def _make_on_page(d: ReportData, report_label: str):
    def _on_page(canvas, doc):
        canvas.saveState()
        # Header
        canvas.setFillColor(C_DARK)
        canvas.rect(0, H - 22 * mm, W, 22 * mm, fill=1, stroke=0)
        canvas.setFillColor(C_WHITE)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawString(MARGIN, H - 14 * mm, f"SAAR v{d.saar_version} — {report_label}")
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(W - MARGIN, H - 14 * mm, d.filename)
        # Footer
        canvas.setFillColor(C_LGREY)
        canvas.rect(0, 0, W, 16 * mm, fill=1, stroke=0)
        canvas.setFillColor(C_GREY)
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(MARGIN, 9 * mm, f"Generated {d.generated_at_display}  |  Python Statistical Engine  |  AI Explanation Layer")
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawRightString(W - MARGIN, 9 * mm, f"Page {doc.page}")
        canvas.restoreState()
    return _on_page


# ── Cover page ─────────────────────────────────────────────────────────────────

def _cover_page(d: ReportData, report_label: str, st: dict) -> List:
    elems = []
    # Dark cover background drawn via canvas — we approximate with a large blue spacer table
    cover_data = [
        [Paragraph("SAAR", st["cover_title"])],
        [Paragraph(report_label, st["cover_sub"])],
        [Spacer(1, 8 * mm)],
        [Paragraph(d.filename, st["cover_file"])],
        [Paragraph(f"Generated {d.generated_at_display}", st["cover_sub"])],
        [Spacer(1, 12 * mm)],
    ]
    cover_tbl = Table(cover_data, colWidths=[CONTENT_W])
    cover_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_DARK),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 24),
        ("RIGHTPADDING", (0, 0), (-1, -1), 24),
    ]))
    elems.append(Spacer(1, 20 * mm))
    elems.append(cover_tbl)
    elems.append(Spacer(1, 8 * mm))

    # Metadata grid
    meta = [
        [_meta_cell("Report Type", d.report_type.title(), st),
         _meta_cell("SAAR Version", f"v{d.saar_version}", st),
         _meta_cell("Records", f"{d.rows:,}", st),
         _meta_cell("Columns", str(d.columns), st)],
    ]
    meta_tbl = Table(meta, colWidths=[CONTENT_W / 4] * 4)
    meta_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_BLUE),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, HexColor("#2a4a7f")),
        ("BOX", (0, 0), (-1, -1), 0, C_BLUE),
    ]))
    elems.append(meta_tbl)
    elems.append(PageBreak())
    return elems


def _meta_cell(label: str, value: str, st: dict) -> Paragraph:
    return Paragraph(
        f'<font color="#aab4c4" size="7">{label}</font><br/>'
        f'<font color="white" size="12"><b>{value}</b></font>',
        ParagraphStyle("mc", fontName="Helvetica", fontSize=10,
                       alignment=TA_CENTER, textColor=C_WHITE, leading=16)
    )


# ── Section header helper ──────────────────────────────────────────────────────

def _section_header(title: str, st: dict) -> List:
    return [
        Paragraph(title, st["h2"]),
        HRFlowable(width=CONTENT_W, thickness=1.5, color=C_BLUE, spaceAfter=8),
    ]


# ── Stats grid ────────────────────────────────────────────────────────────────

def _stats_table(cells: List[Tuple[str, str]], st: dict) -> Table:
    """cells = [(label, value), ...]"""
    data = [[
        Paragraph(f'<font size="7" color="#64748b">{_e(lbl)}</font><br/>'
                  f'<font size="16" color="#0f3460"><b>{_e(val)}</b></font>', st["center"])
        for lbl, val in cells
    ]]
    col_w = CONTENT_W / max(len(cells), 1)
    tbl = Table(data, colWidths=[col_w] * len(cells))
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_LGREY),
        ("BOX", (0, 0), (-1, -1), 0.5, C_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, C_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [C_LGREY]),
    ]))
    return tbl


# ── Bar chart (ReportLab Drawing) ────────────────────────────────────────────

def _bar_chart_drawing(values: list, labels: list, color: "HexColor" = C_BLUE, width: float = 200, height: float = 60) -> Optional[Drawing]:
    if not values or all(v == 0 for v in values):
        return None
    max_v = max(abs(v) for v in values) or 1
    n = len(values)
    gap = 4
    bar_w = max(6, (width - (n - 1) * gap) / n)
    d = Drawing(width, height + 20)
    for i, (v, lbl) in enumerate(zip(values, labels)):
        x = i * (bar_w + gap)
        h = (abs(v) / max_v) * height
        r = Rect(x, 20, bar_w, h, fillColor=color, strokeColor=None)
        d.add(r)
        short = str(lbl)[:7]
        d.add(String(x + bar_w / 2, 2, short, fontSize=6, textAnchor="middle",
                     fillColor=C_GREY, fontName="Helvetica"))
    return d


# ── Helper for Limitations ────────────────────────────────────────────────────

def _add_limitations_section(story: List, d: ReportData, st: dict):
    if not d.has_statistical_limitations:
        return
    story.extend(_section_header("Statistical Limitations", st))
    story.append(Paragraph(f'<font color="#b45309"><b>{_e(d.reliability_explanation)}</b></font>', st["body"]))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph("Because of the limited sample size:", st["body"]))
    for w in d.reliability_warnings:
        story.append(Paragraph(f"• {_e(w)}", st["bullet"]))
    if d.reliability_actions:
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph("<b>Recommended Actions:</b>", st["body"]))
        for a in d.reliability_actions:
            story.append(Paragraph(f"✓ {_e(a)}", st["bullet"]))
    story.append(Spacer(1, 6 * mm))


def _e(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ── Technical PDF ─────────────────────────────────────────────────────────────

def render_technical(d: ReportData) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=28 * mm, bottomMargin=22 * mm,
        title=f"SAAR Technical Report — {d.filename}",
        author="SAAR v1",
    )
    st = _styles()
    story = []

    # Cover
    story.extend(_cover_page(d, "Technical Analysis Report", st))

    # 1. Overview
    story.extend(_section_header("1. Dataset Overview", st))
    story.append(_stats_table([
        ("Total Records", f"{d.rows:,}"),
        ("Columns", str(d.columns)),
        ("Missing Cells", f"{d.missing_total:,}"),
        ("Duplicate Rows", str(d.duplicates)),
        ("File Format", d.file_format.upper()),
    ], st))
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(d.executive_summary, st["body"]))
    story.append(Spacer(1, 6 * mm))

    # Limitations
    _add_limitations_section(story, d, st)

    # 2. Quality
    story.extend(_section_header("2. Data Quality Assessment", st))
    sc = d.quality_score
    score_col = _score_color(sc)
    status = "Excellent" if sc >= 80 else "Requires Attention" if sc >= 60 else "Needs Cleaning"
    story.append(Paragraph(
        f'<font size="10"><b>Score: <font color="{score_col.hexval()}">{sc}/100</font> — {status}</b></font>',
        st["body"]
    ))
    story.append(Paragraph(d.quality_explanation, st["body"]))
    for r in d.quality_reasons:
        story.append(Paragraph(f"• {r}", st["bullet"]))
    story.append(Spacer(1, 6 * mm))

    # 3. Cleaning
    story.extend(_section_header("3. Cleaning Summary", st))
    if d.cleaning_history:
        for i, h in enumerate(d.cleaning_history, 1):
            story.append(Paragraph(f"<b>Pipeline #{i} — {h.get('timestamp','')}</b>", st["h3"]))
            tdata = [["Operation", "Column", "Strategy"]]
            for op in h.get("operations", []):
                tdata.append([
                    op.get("type", "").replace("_", " ").title(),
                    op.get("column", "—"), op.get("strategy", "—")
                ])
            tbl = Table(tdata, colWidths=[CONTENT_W * 0.35, CONTENT_W * 0.35, CONTENT_W * 0.30])
            _style_table(tbl)
            story.append(tbl)
            story.append(Spacer(1, 4 * mm))
    else:
        story.append(Paragraph("No cleaning operations have been applied.", st["body"]))
    story.append(Spacer(1, 4 * mm))

    # 4. Column profiles
    story.extend(_section_header("4. Column Profile Registry", st))
    pdata = [["Column", "Type", "Dtype", "Missing", "Unique", "Key Stats", "Outliers"]]
    for p in d.column_profiles:
        out = f"{p.outlier_count} ({p.outlier_pct}%)" if p.semantic_type == "numeric" else "N/A"
        pdata.append([
            Paragraph(f"<b>{_e(p.name)}</b>", st["small"]),
            p.semantic_type, p.pandas_type,
            f"{p.null_count} ({p.null_pct}%)", str(p.unique_count),
            Paragraph(_e(p.stats_summary[:60]), st["small"]), out,
        ])
    col_ws = [CONTENT_W*0.15, CONTENT_W*0.10, CONTENT_W*0.10, CONTENT_W*0.10,
              CONTENT_W*0.08, CONTENT_W*0.35, CONTENT_W*0.12]
    tbl = Table(pdata, colWidths=col_ws, repeatRows=1)
    _style_table(tbl)
    story.append(tbl)
    story.append(Spacer(1, 6 * mm))

    # 5. Descriptive stats
    num_profiles = [p for p in d.column_profiles if p.semantic_type == "numeric"]
    if num_profiles:
        story.extend(_section_header("5. Descriptive Statistics (Numeric Columns)", st))
        sdata = [["Column", "Statistics", "Outliers", "Missing"]]
        for p in num_profiles:
            sdata.append([
                Paragraph(f"<b>{_e(p.name)}</b>", st["small"]),
                Paragraph(_e(p.stats_summary), st["small"]),
                f"{p.outlier_count} ({p.outlier_pct}%)",
                f"{p.null_count} ({p.null_pct}%)",
            ])
        tbl = Table(sdata, colWidths=[CONTENT_W*0.18, CONTENT_W*0.50, CONTENT_W*0.16, CONTENT_W*0.16], repeatRows=1)
        _style_table(tbl)
        story.append(tbl)
    else:
        story.append(Paragraph("No numeric columns found.", st["body"]))
    story.append(Spacer(1, 6 * mm))

    # 6. Charts
    story.extend(_section_header("6. Column Distributions", st))
    chart_count = 0
    for p in d.column_profiles:
        if chart_count >= 6:
            break
        drawing = None
        if p.semantic_type == "numeric" and p.histogram:
            drawing = _bar_chart_drawing(p.histogram, ["Min","Q1","Med","Q3","Max"])
        elif p.semantic_type in ("categorical","boolean") and p.top_categories:
            vals = [c.get("count", c.get("percentage", 0)) for c in p.top_categories[:6]]
            lbls = [c["value"] for c in p.top_categories[:6]]
            drawing = _bar_chart_drawing(vals, lbls, color=C_GREEN)
        if drawing:
            story.append(KeepTogether([
                Paragraph(f"<b>{_e(p.name)}</b> — {_e(p.semantic_type)}", st["caption"]),
                drawing,
                Spacer(1, 6 * mm),
            ]))
            chart_count += 1
    if chart_count == 0:
        story.append(Paragraph("No chart data available.", st["body"]))
    story.append(Spacer(1, 4 * mm))

    # 7. Findings
    story.extend(_section_header("7. Key Findings & Insights", st))
    for i, f in enumerate(d.key_findings, 1):
        story.append(Paragraph(f"<b>{i:02d}.</b> {_e(f)}", st["bullet"]))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("<b>Business Risks</b>", st["h3"]))
    for r in d.risks:
        story.append(Paragraph(f"⚠ {_e(r)}", st["bullet"]))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("<b>Opportunities</b>", st["h3"]))
    for o in d.opportunities:
        story.append(Paragraph(f"↗ {_e(o)}", st["bullet"]))
    story.append(Spacer(1, 6 * mm))

    # 8. Hypothesis tests
    story.extend(_section_header("8. Hypothesis Tests", st))
    if d.hypothesis_tests:
        tdata = [["Test", "Type", "Variables", "Statistic", "P-Value", "Result"]]
        for t in d.hypothesis_tests:
            stat_str = f"{t.statistic:.4f}" if t.statistic is not None else "N/A"
            pval_str = f"{t.p_value:.4f}" if t.p_value is not None else "N/A"
            sig_str = "Significant ★" if t.significant else "Not Significant"
            tdata.append([
                Paragraph(_e(t.test_name[:40]), st["small"]),
                t.test_type,
                Paragraph(_e(", ".join(t.variables)[:40]), st["small"]),
                stat_str, pval_str, sig_str,
            ])
        col_ws = [CONTENT_W*0.25, CONTENT_W*0.13, CONTENT_W*0.18, CONTENT_W*0.10, CONTENT_W*0.10, CONTENT_W*0.24]
        tbl = Table(tdata, colWidths=col_ws, repeatRows=1)
        _style_table(tbl)
        story.append(tbl)
    else:
        story.append(Paragraph("No hypothesis tests were performed.", st["body"]))
    story.append(Spacer(1, 6 * mm))

    # 9. Modelling
    story.extend(_section_header("9. Modelling Recommendations", st))
    if not d.can_model:
        action_str = ", ".join(d.reliability_actions)
        story.append(Paragraph(f'<font color="{C_RED.hexval()}"><b>Modeling is not recommended due to limited sample size: {_e(d.reliability_explanation)}</b></font>', st["body"]))
        story.append(Paragraph(f"Recommended actions: {action_str}", st["body"]))
    elif d.potential_targets:
        for t in d.potential_targets:
            story.append(Paragraph(
                f"<b>{_e(t['column'])}</b> — {_e(t.get('task',''))} | "
                f"Models: {_e(', '.join(t.get('suggested_models',[])))}",
                st["bullet"]
            ))
            if t.get("reasoning"):
                story.append(Paragraph(_e(t["reasoning"]), st["small"]))
    elif d.unsupervised_recs:
        for u in d.unsupervised_recs:
            story.append(Paragraph(f"<b>{_e(u.get('task',''))}</b> — {_e(u.get('reasoning',''))}", st["bullet"]))
    else:
        story.append(Paragraph("No modelling recommendations available.", st["body"]))
    story.append(Spacer(1, 6 * mm))

    # 10. Methodology
    story.extend(_section_header("10. Methodology", st))
    story.append(Paragraph(d.methodology, st["methodology"]))
    story.append(Spacer(1, 6 * mm))

    # 11. Final Summary
    _add_final_summary(story, d, st)

    doc.build(story, onFirstPage=_make_on_page(d, "Technical Report"),
              onLaterPages=_make_on_page(d, "Technical Report"))
    return buf.getvalue()


# ── Executive PDF ─────────────────────────────────────────────────────────────

def render_executive(d: ReportData) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=28 * mm, bottomMargin=22 * mm,
        title=f"SAAR Executive Report — {d.filename}",
        author="SAAR v1",
    )
    st = _styles()
    story = []

    # Cover
    story.extend(_cover_page(d, "Executive Summary Report", st))

    # 1. Overview
    story.extend(_section_header("1. Executive Overview", st))
    sc = d.quality_score
    sc_col = _score_color(sc)
    story.append(_stats_table([
        ("Quality Score", f"{sc}/100"),
        ("Records", f"{d.rows:,}"),
        ("Columns", str(d.columns)),
        ("Key Findings", str(len(d.key_findings))),
    ], st))
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(d.executive_summary, st["body"]))
    story.append(Spacer(1, 6 * mm))

    # Limitations
    _add_limitations_section(story, d, st)

    # 2. Dataset health
    story.extend(_section_header("2. Dataset Health", st))
    status = "Excellent" if sc >= 80 else "Requires Attention" if sc >= 60 else "Needs Cleaning"
    story.append(Paragraph(
        f'<font size="11"><b>Score: <font color="{sc_col.hexval()}">{sc}/100</font> — {status}</b></font>',
        st["body"]
    ))
    story.append(Paragraph(d.quality_explanation, st["body"]))
    for r in d.quality_reasons[:5]:
        story.append(Paragraph(f"• {_e(r)}", st["bullet"]))
    story.append(Spacer(1, 6 * mm))

    # 3. Key findings
    story.extend(_section_header("3. Key Insights", st))
    for i, f in enumerate(d.key_findings, 1):
        story.append(Paragraph(f"<b>{i:02d}.</b> {_e(f)}", st["bullet"]))
    story.append(Spacer(1, 6 * mm))

    # 4. Charts (top 4)
    story.extend(_section_header("4. Data Visualisations", st))
    chart_count = 0
    for p in d.column_profiles:
        if chart_count >= 4:
            break
        drawing = None
        if p.semantic_type == "numeric" and p.histogram:
            drawing = _bar_chart_drawing(p.histogram, ["Min","Q1","Med","Q3","Max"])
        elif p.semantic_type in ("categorical","boolean") and p.top_categories:
            vals = [c.get("count", c.get("percentage",0)) for c in p.top_categories[:6]]
            lbls = [c["value"] for c in p.top_categories[:6]]
            drawing = _bar_chart_drawing(vals, lbls, color=C_GREEN)
        if drawing:
            story.append(KeepTogether([
                Paragraph(f"<b>{_e(p.name)}</b> — {_e(p.semantic_type)}", st["caption"]),
                drawing,
                Spacer(1, 6 * mm),
            ]))
            chart_count += 1
    story.append(Spacer(1, 4 * mm))

    # 5. Risks & opportunities
    story.extend(_section_header("5. Business Risks & Opportunities", st))
    story.append(Paragraph("<b>Business Risks</b>", st["h3"]))
    for r in d.risks:
        story.append(Paragraph(f"⚠ {_e(r)}", st["bullet"]))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("<b>Opportunities</b>", st["h3"]))
    for o in d.opportunities:
        story.append(Paragraph(f"↗ {_e(o)}", st["bullet"]))
    story.append(Spacer(1, 6 * mm))

    # 6. Recommendations
    story.extend(_section_header("6. Recommendations", st))
    if not d.can_model:
        action_str = ", ".join(d.reliability_actions)
        story.append(Paragraph(f'<font color="{C_RED.hexval()}"><b>Modeling is not recommended due to limited sample size: {_e(d.reliability_explanation)}</b></font>', st["body"]))
        story.append(Paragraph(f"Recommended actions: {action_str}", st["body"]))
    elif d.potential_targets:
        for t in d.potential_targets:
            story.append(Paragraph(
                f"<b>{_e(t['column'])}</b> is a strong candidate for {_e(t.get('task',''))} modelling. "
                f"Recommended: {_e(', '.join(t.get('suggested_models', [])))}.",
                st["bullet"]
            ))
    elif d.unsupervised_recs:
        for u in d.unsupervised_recs:
            story.append(Paragraph(f"<b>{_e(u.get('task',''))}</b>: {_e(u.get('reasoning',''))}", st["bullet"]))
    else:
        story.append(Paragraph("Continue with data cleaning before selecting a modelling approach.", st["body"]))
    story.append(Spacer(1, 6 * mm))

    # 7. Methodology
    story.extend(_section_header("7. Methodology", st))
    story.append(Paragraph(d.methodology, st["methodology"]))
    story.append(Spacer(1, 6 * mm))

    # 8. Final Summary
    _add_final_summary(story, d, st)

    doc.build(story, onFirstPage=_make_on_page(d, "Executive Report"),
              onLaterPages=_make_on_page(d, "Executive Report"))
    return buf.getvalue()


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _style_table(tbl: Table):
    tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), C_DARK),
        ("TEXTCOLOR",    (0, 0), (-1, 0), C_WHITE),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0), 8),
        ("TOPPADDING",   (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING",(0, 0), (-1, 0), 8),
        ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",     (0, 1), (-1, -1), 8),
        ("TOPPADDING",   (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 1), (-1, -1), 6),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [C_WHITE, C_LGREY]),
        ("GRID",         (0, 0), (-1, -1), 0.4, C_BORDER),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
    ]))


def _add_final_summary(story: list, d: ReportData, st: dict):
    story.extend(_section_header("Final Summary", st))
    critical = len(d.quality_reasons)
    status = "Ready for Analysis" if d.quality_score >= 80 else "Needs Cleaning" if d.quality_score >= 60 else "Requires Significant Cleaning"
    cells = [
        ("Quality Score", f"{d.quality_score}/100"),
        ("Quality Issues", str(critical)),
        ("Key Findings", str(len(d.key_findings))),
        ("Analysis Status", status[:18]),
        ("Risks", str(len(d.risks))),
        ("Opportunities", str(len(d.opportunities))),
    ]
    story.append(_stats_table(cells, st))
    story.append(Spacer(1, 6 * mm))
