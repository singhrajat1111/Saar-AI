"""
html_renderer.py
────────────────
Generates self-contained, professional HTML reports from ReportData.
No external fonts or resources — fully offline-compatible.
Two variants: Technical (full detail) and Executive (business-focused).
"""
from __future__ import annotations

import html as _html
from typing import List
from app.core.reports.data_compiler import ReportData, ColumnProfile

# ── Shared CSS ─────────────────────────────────────────────────────────────────
_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: -apple-system, Arial, Helvetica, sans-serif;
    font-size: 14px; line-height: 1.65; color: #1a1a2e;
    background: #f4f6fa; padding: 0;
}
.page-wrap { max-width: 1000px; margin: 0 auto; padding: 32px 20px; }
/* Cover */
.cover {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    color: #fff; padding: 64px 48px; margin-bottom: 32px;
    border-radius: 12px;
}
.cover-title { font-size: 36px; font-weight: 700; letter-spacing: -0.5px; margin-bottom: 8px; }
.cover-sub { font-size: 16px; color: rgba(255,255,255,0.7); margin-bottom: 32px; }
.cover-meta { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 32px; }
.cover-meta-item { background: rgba(255,255,255,0.08); border-radius: 8px; padding: 12px 16px; }
.cover-meta-label { font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: rgba(255,255,255,0.55); }
.cover-meta-value { font-size: 15px; font-weight: 600; color: #fff; margin-top: 2px; }
/* TOC */
.toc { background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 24px 28px; margin-bottom: 28px; }
.toc h2 { font-size: 13px; text-transform: uppercase; letter-spacing: 1px; color: #64748b; margin-bottom: 12px; }
.toc ol { padding-left: 20px; }
.toc li { margin-bottom: 6px; }
.toc a { color: #0f3460; text-decoration: none; font-size: 13px; }
.toc a:hover { text-decoration: underline; }
/* Sections */
.section { background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 32px; margin-bottom: 24px; }
h2.section-title {
    font-size: 18px; font-weight: 700; color: #1a1a2e;
    padding-bottom: 12px; margin-bottom: 20px;
    border-bottom: 2px solid #0f3460;
}
h3.sub-title { font-size: 14px; font-weight: 600; color: #334155; margin: 20px 0 10px 0; }
/* Stats grid */
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin-bottom: 24px; }
.stat-card {
    background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;
    padding: 18px; text-align: center;
}
.stat-card .label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px; color: #64748b; }
.stat-card .value { font-size: 28px; font-weight: 700; color: #0f3460; margin: 6px 0 2px; }
.stat-card .sub { font-size: 11px; color: #94a3b8; }
/* Quality score */
.score-badge {
    display: inline-block; border-radius: 50%; width: 80px; height: 80px;
    line-height: 80px; text-align: center; font-size: 26px; font-weight: 700;
    border: 4px solid;
}
.score-good  { border-color: #22c55e; color: #22c55e; }
.score-ok    { border-color: #f59e0b; color: #f59e0b; }
.score-poor  { border-color: #ef4444; color: #ef4444; }
/* Summary box */
.summary-box {
    background: #f0f7ff; border-left: 4px solid #0f3460;
    padding: 18px 22px; border-radius: 0 8px 8px 0;
    font-size: 14px; color: #1e293b; line-height: 1.7;
}
/* Lists */
.finding-list, .risk-list, .opp-list { list-style: none; padding: 0; }
.finding-list li { padding: 10px 12px; margin-bottom: 8px; background: #f8fafc; border-radius: 6px; border-left: 3px solid #0f3460; }
.risk-list li { padding: 10px 12px; margin-bottom: 8px; background: #fff5f5; border-radius: 6px; border-left: 3px solid #ef4444; color: #7f1d1d; }
.opp-list li { padding: 10px 12px; margin-bottom: 8px; background: #f0fdf4; border-radius: 6px; border-left: 3px solid #22c55e; color: #14532d; }
.num { font-weight: 700; color: #0f3460; margin-right: 8px; }
/* Tables */
table { width: 100%; border-collapse: collapse; font-size: 12.5px; margin-top: 8px; }
thead th { background: #1a1a2e; color: #fff; padding: 10px 12px; text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }
tbody tr:nth-child(odd) { background: #f8fafc; }
tbody td { padding: 9px 12px; border-bottom: 1px solid #e2e8f0; color: #334155; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; text-transform: uppercase; }
.badge-numeric   { background: #dbeafe; color: #1e40af; }
.badge-categorical { background: #dcfce7; color: #166534; }
.badge-datetime  { background: #fef9c3; color: #713f12; }
.badge-boolean   { background: #f3e8ff; color: #6b21a8; }
.badge-identifier { background: #fee2e2; color: #991b1b; }
.badge-unknown   { background: #f1f5f9; color: #475569; }
.sig-yes { color: #b91c1c; font-weight: 700; }
.sig-no  { color: #64748b; }
/* Charts */
.chart-container { margin: 12px 0 20px; }
.chart-title { font-size: 11px; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
/* Grid */
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
@media (max-width: 640px) { .two-col { grid-template-columns: 1fr; } .cover-meta { grid-template-columns: 1fr; } }
/* Methodology */
.methodology { background: #fafafa; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; font-size: 13px; color: #475569; line-height: 1.7; font-style: italic; }
/* Final summary */
.summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; }
.summary-item { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; }
.summary-item .s-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px; color: #64748b; margin-bottom: 6px; }
.summary-item .s-value { font-size: 20px; font-weight: 700; color: #1a1a2e; }
/* Footer */
footer { text-align: center; padding: 24px; color: #94a3b8; font-size: 11px; border-top: 1px solid #e2e8f0; margin-top: 32px; }
@media print {
    body { background: #fff; }
    .page-wrap { max-width: 100%; padding: 16px; }
    .cover { break-after: page; }
    .section { break-inside: avoid; }
}
"""


def _e(s: str) -> str:
    """HTML escape."""
    return _html.escape(str(s))


def _score_class(score: int) -> str:
    if score >= 80: return "score-good"
    if score >= 60: return "score-ok"
    return "score-poor"


def _badge(stype: str) -> str:
    cls = f"badge-{stype}" if stype in ("numeric","categorical","datetime","boolean","identifier") else "badge-unknown"
    return f'<span class="badge {cls}">{_e(stype)}</span>'


def _svg_bar_chart(values: list, labels: list, color: str = "#0f3460", max_h: int = 60) -> str:
    """Generate a minimal inline SVG bar chart."""
    if not values or all(v == 0 for v in values):
        return ""
    max_v = max(abs(v) for v in values) or 1
    w_total = 280
    bar_w = max(8, (w_total - len(values) * 4) // len(values))
    gap = 4
    svg_w = len(values) * (bar_w + gap)
    svg_h = max_h + 28

    bars = []
    for i, (v, lbl) in enumerate(zip(values, labels)):
        h = int((abs(v) / max_v) * max_h)
        x = i * (bar_w + gap)
        y = max_h - h
        short_lbl = str(lbl)[:8]
        bars.append(f'<rect x="{x}" y="{y}" width="{bar_w}" height="{h}" fill="{color}" rx="2" opacity="0.85"/>')
        bars.append(f'<text x="{x + bar_w//2}" y="{max_h + 14}" text-anchor="middle" font-size="8" fill="#64748b" font-family="Arial,sans-serif">{_e(short_lbl)}</text>')

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}" height="{svg_h}" '
        f'style="display:block;overflow:visible;">'
        + "".join(bars) +
        f'</svg>'
    )


def _render_column_charts_section(profiles: list) -> str:
    """Render top-N column charts section."""
    html_parts = []
    shown = 0
    for p in profiles:
        if shown >= 8:
            break
        chart_svg = ""
        if p.semantic_type == "numeric" and p.histogram:
            labels = ["Min", "Q1", "Median", "Q3", "Max"]
            chart_svg = _svg_bar_chart(p.histogram, labels)
        elif p.semantic_type in ("categorical", "boolean") and p.top_categories:
            vals = [c["count"] if "count" in c else c.get("percentage", 0) for c in p.top_categories[:6]]
            labels = [c["value"] for c in p.top_categories[:6]]
            chart_svg = _svg_bar_chart(vals, labels, color="#166534")
        if chart_svg:
            html_parts.append(f"""
            <div style="margin-bottom:24px;">
              <div class="chart-title">{_e(p.name)} — {_e(p.semantic_type)}</div>
              <div class="chart-container">{chart_svg}</div>
            </div>""")
            shown += 1
    if not html_parts:
        return "<p style='color:#94a3b8;font-size:13px;'>No chart data available.</p>"
    return "\n".join(html_parts)


def _cover(d: ReportData) -> str:
    rtype_label = "Technical Analysis Report" if d.report_type == "technical" else "Executive Summary Report"
    return f"""
    <div class="cover">
      <div class="cover-title">SAAR</div>
      <div class="cover-sub">{_e(rtype_label)}</div>
      <div style="font-size:22px;font-weight:600;margin-bottom:4px;">{_e(d.filename)}</div>
      <div style="font-size:14px;color:rgba(255,255,255,0.6);">Generated {_e(d.generated_at_display)}</div>
      <div class="cover-meta">
        <div class="cover-meta-item"><div class="cover-meta-label">Report Type</div><div class="cover-meta-value">{_e(d.report_type.title())}</div></div>
        <div class="cover-meta-item"><div class="cover-meta-label">SAAR Version</div><div class="cover-meta-value">v{_e(d.saar_version)}</div></div>
        <div class="cover-meta-item"><div class="cover-meta-label">Total Records</div><div class="cover-meta-value">{d.rows:,}</div></div>
        <div class="cover-meta-item"><div class="cover-meta-label">Total Columns</div><div class="cover-meta-value">{d.columns}</div></div>
      </div>
    </div>"""


def _footer(d: ReportData) -> str:
    return f"""
    <footer>
      <strong>Generated by SAAR v{_e(d.saar_version)}</strong> &mdash; Python Statistical Engine &mdash; AI Explanation Layer<br>
      {_e(d.generated_at_display)} &mdash; All statistical values are produced by the Python Statistical Engine.
      AI was used only to improve natural language clarity.
    </footer>"""


def _final_summary(d: ReportData) -> str:
    critical = len([r for r in d.quality_reasons if r]) if d.quality_reasons else 0
    rec_actions = len(d.key_findings)
    score_class = "score-good" if d.quality_score >= 80 else ("score-ok" if d.quality_score >= 60 else "score-poor")
    score_color = "#22c55e" if d.quality_score >= 80 else ("#f59e0b" if d.quality_score >= 60 else "#ef4444")
    status = "Ready for Analysis" if d.quality_score >= 80 else ("Needs Cleaning" if d.quality_score >= 60 else "Requires Significant Cleaning")
    return f"""
    <section class="section" id="summary">
      <h2 class="section-title">Final Summary</h2>
      <div class="summary-grid">
        <div class="summary-item">
          <div class="s-label">Data Quality Score</div>
          <div class="s-value" style="color:{score_color};">{d.quality_score}/100</div>
        </div>
        <div class="summary-item">
          <div class="s-label">Quality Observations</div>
          <div class="s-value">{critical}</div>
        </div>
        <div class="summary-item">
          <div class="s-label">Key Findings</div>
          <div class="s-value">{rec_actions}</div>
        </div>
        <div class="summary-item">
          <div class="s-label">Analysis Status</div>
          <div class="s-value" style="font-size:14px;margin-top:4px;">{_e(status)}</div>
        </div>
        <div class="summary-item">
          <div class="s-label">Risks Identified</div>
          <div class="s-value">{len(d.risks)}</div>
        </div>
        <div class="summary-item">
          <div class="s-label">Opportunities</div>
          <div class="s-value">{len(d.opportunities)}</div>
        </div>
      </div>
    </section>"""


def _wrap_html(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{_e(title)}</title>
  <style>{_CSS}</style>
</head>
<body>
<div class="page-wrap">
{body}
</div>
</body>
</html>"""


# ── Helper for Limitations ────────────────────────────────────────────────────

def _render_limitations(d: ReportData) -> str:
    if not d.has_statistical_limitations:
        return ""
    bullets_li = "".join(f'<li style="padding: 8px 12px; margin-bottom: 6px; background: #fffaf0; border-radius: 6px; border-left: 3px solid #f59e0b; color: #78350f;">• {_e(b)}</li>' for b in d.reliability_warnings)
    actions_li = "".join(f'<li style="padding: 8px 12px; margin-bottom: 6px; background: #f0fdf4; border-radius: 6px; border-left: 3px solid #22c55e; color: #14532d;">✔ {_e(a)}</li>' for a in d.reliability_actions)
    
    actions_html = ""
    if actions_li:
        actions_html = f'<h3 class="sub-title" style="margin-top:16px;">Recommended Actions</h3><ul style="list-style:none; padding:0;">{actions_li}</ul>'
        
    return f"""
    <section class="section" id="limitations">
      <h2 class="section-title" style="border-bottom: 2px solid #f59e0b; color:#b45309;">Statistical Limitations</h2>
      <p style="margin-bottom:12px; font-weight:600; color:#b45309;">{_e(d.reliability_explanation)}</p>
      <p style="margin-bottom:8px; font-weight:600; color:#475569;">Because of the limited sample size:</p>
      <ul style="list-style:none; padding:0;">
        {bullets_li}
      </ul>
      {actions_html}
    </section>"""


# ── Technical Report ──────────────────────────────────────────────────────────

def render_technical(d: ReportData) -> str:
    # TOC
    toc_items = [
        ("overview", "1. Dataset Overview"),
        ("limitations", "2. Statistical Limitations"),
        ("quality", "3. Data Quality Assessment"),
        ("cleaning", "4. Cleaning Summary"),
        ("profiles", "5. Column Profile Registry"),
        ("stats", "6. Statistical Analysis"),
        ("charts", "7. Column Distributions"),
        ("findings", "8. Key Findings & Insights"),
        ("tests", "9. Hypothesis Tests"),
        ("ml", "10. Modelling Recommendations"),
        ("methodology", "11. Methodology"),
        ("summary", "12. Final Summary"),
    ]
    toc_html = "<ol>" + "".join(f'<li><a href="#{i}">{_e(t)}</a></li>' for i, t in toc_items) + "</ol>"

    # 1. Overview
    overview = f"""
    <section class="section" id="overview">
      <h2 class="section-title">1. Dataset Overview</h2>
      <div class="stats-grid">
        <div class="stat-card"><div class="label">Total Records</div><div class="value">{d.rows:,}</div></div>
        <div class="stat-card"><div class="label">Columns</div><div class="value">{d.columns}</div></div>
        <div class="stat-card"><div class="label">Missing Cells</div><div class="value">{d.missing_total:,}</div></div>
        <div class="stat-card"><div class="label">Duplicate Rows</div><div class="value">{d.duplicates:,}</div></div>
        <div class="stat-card"><div class="label">File Format</div><div class="value" style="font-size:18px;">{_e(d.file_format.upper())}</div></div>
      </div>
      <div class="summary-box">{_e(d.executive_summary)}</div>
    </section>"""

    # 3. Quality
    reasons_li = "".join(f"<li>{_e(r)}</li>" for r in d.quality_reasons) or "<li>No specific deductions recorded.</li>"
    score_cls = _score_class(d.quality_score)
    quality = f"""
    <section class="section" id="quality">
      <h2 class="section-title">3. Data Quality Assessment</h2>
      <div style="display:flex;align-items:center;gap:24px;margin-bottom:20px;">
        <div class="score-badge {score_cls}">{d.quality_score}</div>
        <div><strong>Score: {d.quality_score}/100</strong><p style="color:#64748b;font-size:13px;margin-top:4px;">{_e(d.quality_explanation)}</p></div>
      </div>
      <h3 class="sub-title">Quality Observations</h3>
      <ul class="finding-list">{reasons_li}</ul>
    </section>"""

    # 4. Cleaning
    if d.cleaning_history:
        ops_html = ""
        for i, h in enumerate(d.cleaning_history, 1):
            ops_rows = "".join(
                f"<tr><td>{_e(op.get('type','').replace('_',' ').title())}</td>"
                f"<td>{_e(op.get('column','—'))}</td>"
                f"<td>{_e(op.get('strategy','—'))}</td></tr>"
                for op in h.get("operations", [])
            )
            ops_html += f"""
            <h3 class="sub-title">Pipeline #{i} — {_e(h.get('timestamp',''))}</h3>
            <table><thead><tr><th>Operation</th><th>Column</th><th>Strategy</th></tr></thead>
            <tbody>{ops_rows}</tbody></table>"""
        cleaning = f'<section class="section" id="cleaning"><h2 class="section-title">4. Cleaning Summary</h2>{ops_html}</section>'
    else:
        cleaning = '<section class="section" id="cleaning"><h2 class="section-title">4. Cleaning Summary</h2><p style="color:#94a3b8;">No cleaning operations applied.</p></section>'

    # 5. Column profiles
    profile_rows = ""
    for p in d.column_profiles:
        out_text = f"{p.outlier_count} ({p.outlier_pct}%)" if p.semantic_type == "numeric" else "N/A"
        profile_rows += f"""
        <tr>
          <td><strong style="font-family:monospace;">{_e(p.name)}</strong></td>
          <td>{_badge(p.semantic_type)}</td>
          <td><code>{_e(p.pandas_type)}</code></td>
          <td>{p.null_count} ({p.null_pct}%)</td>
          <td>{p.unique_count}</td>
          <td style="font-size:11.5px;">{_e(p.stats_summary)}</td>
          <td>{_e(out_text)}</td>
        </tr>"""
    profiles_section = f"""
    <section class="section" id="profiles">
      <h2 class="section-title">5. Column Profile Registry</h2>
      <table>
        <thead><tr>
          <th>Column</th><th>Type</th><th>Dtype</th>
          <th>Missing</th><th>Unique</th><th>Key Statistics</th><th>Outliers</th>
        </tr></thead>
        <tbody>{profile_rows}</tbody>
      </table>
    </section>"""

    # 6. Stats (numeric detail)
    num_profiles = [p for p in d.column_profiles if p.semantic_type == "numeric"]
    if num_profiles:
        num_rows = "".join(
            f"<tr><td><strong style='font-family:monospace;'>{_e(p.name)}</strong></td>"
            f"<td>{_e(p.stats_summary)}</td>"
            f"<td>{p.outlier_count} ({p.outlier_pct}%)</td>"
            f"<td>{p.null_count} ({p.null_pct}%)</td></tr>"
            for p in num_profiles
        )
        stats_section = f"""
        <section class="section" id="stats">
          <h2 class="section-title">6. Statistical Analysis (Numeric)</h2>
          <table>
            <thead><tr><th>Column</th><th>Statistics</th><th>Outliers</th><th>Missing</th></tr></thead>
            <tbody>{num_rows}</tbody>
          </table>
        </section>"""
    else:
        stats_section = '<section class="section" id="stats"><h2 class="section-title">6. Statistical Analysis</h2><p style="color:#94a3b8;">No numeric columns found.</p></section>'

    # 7. Charts
    charts_section = f"""
    <section class="section" id="charts">
      <h2 class="section-title">7. Column Distributions</h2>
      {_render_column_charts_section(d.column_profiles)}
    </section>"""

    # 8. Findings
    findings_li = "".join(f'<li><span class="num">{i:02d}.</span>{_e(f)}</li>' for i, f in enumerate(d.key_findings, 1)) or "<li>No findings available.</li>"
    risk_li = "".join(f"<li>⚠ {_e(r)}</li>" for r in d.risks) or "<li>No risks identified.</li>"
    opp_li = "".join(f"<li>↗ {_e(o)}</li>" for o in d.opportunities) or "<li>No opportunities identified.</li>"
    findings_section = f"""
    <section class="section" id="findings">
      <h2 class="section-title">8. Key Findings & Insights</h2>
      <ul class="finding-list">{findings_li}</ul>
      <div class="two-col" style="margin-top:20px;">
        <div>
          <h3 class="sub-title">Business Risks & Warnings</h3>
          <ul class="risk-list">{risk_li}</ul>
        </div>
        <div>
          <h3 class="sub-title">Opportunities & Next Steps</h3>
          <ul class="opp-list">{opp_li}</ul>
        </div>
      </div>
    </section>"""

    # 9. Hypothesis tests
    if d.hypothesis_tests:
        test_rows = "".join(
            f"""<tr>
              <td style="font-size:11.5px;">{_e(t.test_name)}</td>
              <td><span class="badge badge-numeric">{_e(t.test_type)}</span></td>
              <td style="font-size:11px;">{_e(', '.join(t.variables))}</td>
              <td style="font-family:monospace;">{f'{t.statistic:.4f}' if t.statistic is not None else 'N/A'}</td>
              <td style="font-family:monospace;">{f'{t.p_value:.4f}' if t.p_value is not None else 'N/A'}</td>
              <td class="{'sig-yes' if t.significant else 'sig-no'}">{'Significant ★' if t.significant else 'Not Significant'}</td>
              <td style="font-size:11.5px;">{_e(t.interpretation)}</td>
            </tr>"""
            for t in d.hypothesis_tests
        )
        tests_section = f"""
        <section class="section" id="tests">
          <h2 class="section-title">9. Hypothesis Tests</h2>
          <table>
            <thead><tr><th>Test Name</th><th>Type</th><th>Variables</th><th>Statistic</th><th>P-Value</th><th>Result</th><th>Interpretation</th></tr></thead>
            <tbody>{test_rows}</tbody>
          </table>
        </section>"""
    else:
        tests_section = '<section class="section" id="tests"><h2 class="section-title">9. Hypothesis Tests</h2><p style="color:#94a3b8;">No hypothesis tests were performed on this dataset.</p></section>'

    # 10. ML recommendations
    if not d.can_model:
        action_str = ", ".join(d.reliability_actions)
        ml_section = f"""
        <section class="section" id="ml">
          <h2 class="section-title">10. Modelling Recommendations</h2>
          <p style="color:#ef4444; font-weight:600; margin-bottom:8px;">Modeling is not recommended due to limited sample size: {_e(d.reliability_explanation)}</p>
          <p>Recommended actions: {action_str}</p>
        </section>"""
    elif d.potential_targets:
        ml_rows = "".join(
            f"<tr><td><strong style='font-family:monospace;'>{_e(t['column'])}</strong></td>"
            f"<td>{_e(t.get('task',''))}</td>"
            f"<td>{_e(', '.join(t.get('suggested_models',[])))}</td>"
            f"<td style='font-size:11.5px;'>{_e(t.get('reasoning',''))}</td></tr>"
            for t in d.potential_targets
        )
        ml_section = f"""
        <section class="section" id="ml">
          <h2 class="section-title">10. Modelling Recommendations</h2>
          <table><thead><tr><th>Target Column</th><th>Task</th><th>Suggested Models</th><th>Reasoning</th></tr></thead>
          <tbody>{ml_rows}</tbody></table>
        </section>"""
    elif d.unsupervised_recs:
        ml_section = f"""
        <section class="section" id="ml">
          <h2 class="section-title">10. Modelling Recommendations</h2>
          <ul class="finding-list">{''.join(f'<li>{_e(u.get("task",""))} — {_e(u.get("reasoning",""))} ({_e(", ".join(u.get("suggested_models",[])))})</li>' for u in d.unsupervised_recs)}</ul>
        </section>"""
    else:
        ml_section = '<section class="section" id="ml"><h2 class="section-title">10. Modelling Recommendations</h2><p style="color:#94a3b8;">No modelling recommendations available.</p></section>'

    # 11. Methodology
    method_section = f"""
    <section class="section" id="methodology">
      <h2 class="section-title">11. Methodology</h2>
      <div class="methodology">{_e(d.methodology)}</div>
    </section>"""

    body = (
        _cover(d)
        + f'<div class="toc"><h2>Table of Contents</h2>{toc_html}</div>'
        + overview + _render_limitations(d) + quality + cleaning + profiles_section
        + stats_section + charts_section + findings_section
        + tests_section + ml_section + method_section
        + _final_summary(d)
        + _footer(d)
    )
    return _wrap_html(f"SAAR Technical Report — {d.filename}", body)


# ── Executive Report ──────────────────────────────────────────────────────────

def render_executive(d: ReportData) -> str:
    toc_items = [
        ("overview", "1. Executive Overview"),
        ("limitations", "2. Statistical Limitations"),
        ("health", "3. Dataset Health"),
        ("findings", "4. Key Insights"),
        ("charts", "5. Data Visualisations"),
        ("risks", "6. Business Risks & Opportunities"),
        ("recommendations", "7. Recommendations"),
        ("methodology", "8. Methodology"),
        ("summary", "9. Final Summary"),
    ]
    toc_html = "<ol>" + "".join(f'<li><a href="#{i}">{_e(t)}</a></li>' for i, t in toc_items) + "</ol>"

    # 1. Executive overview
    overview = f"""
    <section class="section" id="overview">
      <h2 class="section-title">1. Executive Overview</h2>
      <div class="stats-grid">
        <div class="stat-card"><div class="label">Quality Score</div><div class="value" style="color:{'#22c55e' if d.quality_score >= 80 else '#f59e0b' if d.quality_score >= 60 else '#ef4444'};">{d.quality_score}</div><div class="sub">out of 100</div></div>
        <div class="stat-card"><div class="label">Total Records</div><div class="value">{d.rows:,}</div></div>
        <div class="stat-card"><div class="label">Data Columns</div><div class="value">{d.columns}</div></div>
        <div class="stat-card"><div class="label">Key Findings</div><div class="value">{len(d.key_findings)}</div></div>
      </div>
      <div class="summary-box">{_e(d.executive_summary)}</div>
    </section>"""

    # 3. Dataset health
    score_cls = _score_class(d.quality_score)
    health_status = "Excellent" if d.quality_score >= 80 else "Requires Attention" if d.quality_score >= 60 else "Needs Cleaning"
    reasons_li = "".join(f"<li>{_e(r)}</li>" for r in d.quality_reasons[:5]) or "<li>No quality deductions.</li>"
    health = f"""
    <section class="section" id="health">
      <h2 class="section-title">3. Dataset Health</h2>
      <div style="display:flex;align-items:center;gap:28px;margin-bottom:20px;">
        <div class="score-badge {score_cls}">{d.quality_score}</div>
        <div>
          <div style="font-size:18px;font-weight:700;color:#1a1a2e;">{_e(health_status)}</div>
          <div style="color:#64748b;font-size:13px;margin-top:4px;">{_e(d.quality_explanation)}</div>
        </div>
      </div>
      <h3 class="sub-title">Quality Observations</h3>
      <ul class="risk-list">{reasons_li}</ul>
    </section>"""

    # 4. Findings
    findings_li = "".join(f'<li><span class="num">{i:02d}.</span>{_e(f)}</li>' for i, f in enumerate(d.key_findings, 1)) or "<li>No findings available.</li>"
    findings = f"""
    <section class="section" id="findings">
      <h2 class="section-title">4. Key Insights</h2>
      <ul class="finding-list">{findings_li}</ul>
    </section>"""

    # 5. Charts (top categorical + top numeric)
    charts = f"""
    <section class="section" id="charts">
      <h2 class="section-title">5. Data Visualisations</h2>
      {_render_column_charts_section(d.column_profiles)}
    </section>"""

    # 6. Risks & opportunities
    risk_li = "".join(f"<li>⚠ {_e(r)}</li>" for r in d.risks) or "<li>No risks identified.</li>"
    opp_li = "".join(f"<li>↗ {_e(o)}</li>" for o in d.opportunities) or "<li>No opportunities identified.</li>"
    risks = f"""
    <section class="section" id="risks">
      <h2 class="section-title">6. Business Risks & Opportunities</h2>
      <div class="two-col">
        <div><h3 class="sub-title">Business Risks</h3><ul class="risk-list">{risk_li}</ul></div>
        <div><h3 class="sub-title">Opportunities</h3><ul class="opp-list">{opp_li}</ul></div>
      </div>
    </section>"""

    # 7. Recommendations (ML targets in business language)
    if not d.can_model:
        action_str = ", ".join(d.reliability_actions)
        recommendations = f"""
        <section class="section" id="recommendations">
          <h2 class="section-title">7. Recommendations</h2>
          <p style="color:#ef4444; font-weight:600; margin-bottom:8px;">Modeling is not recommended due to limited sample size: {_e(d.reliability_explanation)}</p>
          <p>Recommended actions: {action_str}</p>
        </section>"""
    else:
        if d.potential_targets:
            rec_items = "".join(
                f"<li><strong>{_e(t['column'])}</strong> — {_e(t.get('task',''))} ({_e(', '.join(t.get('suggested_models',[])))}) — {_e(t.get('reasoning',''))}</li>"
                for t in d.potential_targets
            )
        elif d.unsupervised_recs:
            rec_items = "".join(
                f"<li><strong>{_e(u.get('task',''))}</strong> — {_e(u.get('reasoning',''))}</li>"
                for u in d.unsupervised_recs
            )
        else:
            rec_items = "<li>Continue with data cleaning before selecting a modelling approach.</li>"
        recommendations = f"""
        <section class="section" id="recommendations">
          <h2 class="section-title">7. Recommendations</h2>
          <ul class="opp-list">{rec_items}</ul>
        </section>"""

    # 8. Methodology
    method = f"""
    <section class="section" id="methodology">
      <h2 class="section-title">8. Methodology</h2>
      <div class="methodology">{_e(d.methodology)}</div>
    </section>"""

    body = (
        _cover(d)
        + f'<div class="toc"><h2>Table of Contents</h2>{toc_html}</div>'
        + overview + _render_limitations(d) + health + findings + charts + risks
        + recommendations + method
        + _final_summary(d)
        + _footer(d)
    )
    return _wrap_html(f"SAAR Executive Report — {d.filename}", body)
