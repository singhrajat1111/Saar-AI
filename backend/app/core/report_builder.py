import json
from typing import Dict, Any

class ReportBuilder:
    """
    Utility class to compile dataset analysis metadata and results
    into download-ready Markdown and styled HTML reports.
    """

    @staticmethod
    def build_pdf_report(dataset: Dict[str, Any], report_type: str = "technical") -> bytes:
        from app.core.reports.data_compiler import compile_report_data
        from app.core.reports.pdf_renderer import render_technical, render_executive
        data = compile_report_data(dataset, report_type)
        if report_type == "executive":
            return render_executive(data)
        return render_technical(data)

    @staticmethod
    def build_markdown_report(dataset: Dict[str, Any]) -> str:
        filename = dataset.get("filename", "Dataset")
        rows = dataset.get("rows_count", 0)
        cols = dataset.get("columns_count", 0)
        missing = dataset.get("missing_values_count", 0)
        duplicates = dataset.get("duplicates_count", 0)
        
        ai_insights = dataset.get("ai_insights", {})
        summary = ai_insights.get("executive_summary", "No executive summary available.")
        findings = ai_insights.get("key_findings", [])
        risks = ai_insights.get("risks", [])
        opportunities = ai_insights.get("opportunities", [])
        
        md = []
        md.append(f"# SAAR AI — Data Analysis Report")
        md.append(f"**Dataset File:** `{filename}`  ")
        md.append(f"**Report Generated:** {dataset.get('cleaning_history', [{'timestamp': 'Initial analysis'}])[-1].get('timestamp', 'N/A')}\n")
        
        md.append("---")
        md.append("## 1. Executive Summary")
        md.append(summary)
        
        md.append("\n## 2. Dataset Overview")
        md.append(f"- **Total Records (Rows):** {rows}")
        md.append(f"- **Attributes (Columns):** {cols}")
        md.append(f"- **Total Missing Cells:** {missing}")
        md.append(f"- **Duplicate Rows:** {duplicates}")
        md.append(f"- **Quality Score:** {ai_insights.get('quality_score', 'N/A')}/100 ({ai_insights.get('quality_score_explanation', '')})")
        
        # Quality score reasons
        reasons = ai_insights.get("quality_score_reasons", [])
        if reasons:
            md.append("\n**Data Quality Observations:**")
            for r in reasons:
                md.append(f"- {r}")

        # Column profiles
        md.append("\n## 3. Attribute (Column) Profiles")
        md.append("| Column Name | Semantic Type | Pandas Type | Null Count | Unique Count | Stats (Mean/Median/Mode) | Outliers Count |")
        md.append("|---|---|---|---|---|---|---|")
        
        schema = dataset.get("schema", [])
        eda = dataset.get("eda", {})
        num_stats = eda.get("numeric_stats", {})
        cat_stats = eda.get("categorical_stats", {})
        
        for col_info in schema:
            cname = col_info["column_name"]
            stype = col_info["semantic_type"]
            ptype = col_info["pandas_dtype"]
            nulls = col_info["null_count"]
            uniques = col_info["unique_values"]
            
            stats_text = "N/A"
            outlier_text = "N/A"
            
            if stype == "numeric" and cname in num_stats:
                ns = num_stats[cname]
                stats_text = f"Mean: {round(ns['mean'], 2)} / Med: {round(ns['median'], 2)}"
                outlier_text = f"{ns['outliers_count']} ({ns['outliers_pct']}%)"
            elif stype in ["categorical", "boolean"] and cname in cat_stats:
                top_cats = cat_stats[cname].get("top_categories", [])
                if top_cats:
                    stats_text = f"Mode: '{top_cats[0]['value']}' ({top_cats[0]['percentage']}%)"
                    
            md.append(f"| {cname} | {stype} | `{ptype}` | {nulls} | {uniques} | {stats_text} | {outlier_text} |")

        # Key Findings
        md.append("\n## 4. Key Analytical Findings")
        for idx, f in enumerate(findings):
            md.append(f"{idx + 1}. {f}")
            
        # Risks & Opportunities
        md.append("\n## 5. Business Risks & Technical Warnings")
        for r in risks:
            md.append(f"- ⚠️ {r}")
            
        md.append("\n## 6. Business Opportunities & Next Steps")
        for opp in opportunities:
            md.append(f"- 💡 {opp}")
            
        # Cleaning History
        history = dataset.get("cleaning_history", [])
        if history:
            md.append("\n## 7. Applied Cleaning Operations")
            for idx, h in enumerate(history):
                md.append(f"**Fix Pipeline #{idx+1} ({h['timestamp']}):**")
                for op in h["operations"]:
                    op_type = op.get("type", "").replace("_", " ").title()
                    col_text = f" on '{op['column']}'" if op.get("column") else ""
                    strat_text = f" (strategy: {op.get('strategy')})" if op.get("strategy") else ""
                    md.append(f"- Applied: **{op_type}**{col_text}{strat_text}")

        # ML Recommendations
        ml_recs = dataset.get("ml_recommendations", {})
        potential_targets = ml_recs.get("potential_targets", [])
        unsupervised = ml_recs.get("unsupervised_recommendations", [])
        
        md.append("\n## 8. Predictive Modeling Recommendations")
        if potential_targets:
            for t in potential_targets:
                md.append(f"- **Suggested Target:** `{t['column']}` ({t['task']})")
                md.append(f"  - Recommended Algorithms: {', '.join(t['suggested_models'])}")
        elif unsupervised:
            for u in unsupervised:
                md.append(f"- **Approach:** {u['task']}")
                md.append(f"  - Reason: {u['reasoning']}")
                md.append(f"  - Recommended: {', '.join(u['suggested_models'])}")
        else:
            md.append("No modeling targets suggested.")

        return "\n".join(md)

    @classmethod
    def build_html_report(cls, dataset: Dict[str, Any]) -> str:
        filename = dataset.get("filename", "Dataset")
        ai_insights = dataset.get("ai_insights", {})
        score = ai_insights.get("quality_score", 100)
        explanation = ai_insights.get("quality_score_explanation", "")
        summary = ai_insights.get("executive_summary", "No summary.")
        
        # Compile lists
        findings_li = "".join(f"<li>{x}</li>" for x in ai_insights.get("key_findings", []))
        risks_li = "".join(f"<li>⚠️ {x}</li>" for x in ai_insights.get("risks", []))
        opp_li = "".join(f"<li>💡 {x}</li>" for x in ai_insights.get("opportunities", []))
        
        # Compile columns rows
        column_rows = []
        schema = dataset.get("schema", [])
        eda = dataset.get("eda", {})
        num_stats = eda.get("numeric_stats", {})
        cat_stats = eda.get("categorical_stats", {})
        
        for col_info in schema:
            cname = col_info["column_name"]
            stype = col_info["semantic_type"]
            ptype = col_info["pandas_dtype"]
            nulls = col_info["null_count"]
            uniques = col_info["unique_values"]
            
            stats_text = "N/A"
            outlier_text = "N/A"
            
            if stype == "numeric" and cname in num_stats:
                ns = num_stats[cname]
                stats_text = f"Mean: {round(ns['mean'], 2)} <br/> Med: {round(ns['median'], 2)}"
                outlier_text = f"{ns['outliers_count']} ({ns['outliers_pct']}%)"
            elif stype in ["categorical", "boolean"] and cname in cat_stats:
                top_cats = cat_stats[cname].get("top_categories", [])
                if top_cats:
                    stats_text = f"Mode: '{top_cats[0]['value']}' <br/> ({top_cats[0]['percentage']}%)"
                    
            row_html = f"""
            <tr>
                <td><strong>{cname}</strong></td>
                <td><span class="badge {stype}">{stype}</span></td>
                <td><code>{ptype}</code></td>
                <td>{nulls}</td>
                <td>{uniques}</td>
                <td>{stats_text}</td>
                <td>{outlier_text}</td>
            </tr>
            """
            column_rows.append(row_html)
            
        column_table_rows = "\n".join(column_rows)
        
        # Color rating based on score
        color_class = "good"
        if score < 50:
            color_class = "poor"
        elif score < 75:
            color_class = "moderate"
            
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>SAAR AI — Executive Analytics Report ({filename})</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            color: #E8EAED;
            background-color: #202124;
            line-height: 1.6;
            margin: 0;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 960px;
            margin: 0 auto;
            background: #2D2F31;
            padding: 40px;
            border-radius: 12px;
            border: 1px border #3C4043;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }}
        h1, h2, h3 {{
            color: #FFFFFF;
            font-weight: 600;
        }}
        h1 {{
            border-bottom: 2px solid #3C4043;
            padding-bottom: 15px;
            margin-top: 0;
            font-size: 28px;
        }}
        h2 {{
            border-bottom: 1px solid #3C4043;
            padding-bottom: 8px;
            margin-top: 30px;
            font-size: 20px;
        }}
        .meta {{
            font-size: 14px;
            color: #9AA0A6;
            margin-bottom: 25px;
        }}
        .grid {{
            display: grid;
            grid-template-cols: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: #202124;
            border: 1px solid #3C4043;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }}
        .card-label {{
            font-size: 12px;
            color: #9AA0A6;
            text-transform: uppercase;
            letter-spacing: 0.8px;
        }}
        .card-value {{
            font-size: 24px;
            font-weight: bold;
            color: #8AB4F8;
            margin-top: 5px;
        }}
        .score-circle {{
            width: 100px;
            height: 100px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 32px;
            font-weight: bold;
            margin: 0 auto 10px auto;
        }}
        .score-circle.good {{
            border: 4px solid #81C995;
            color: #81C995;
        }}
        .score-circle.moderate {{
            border: 4px solid #FDD663;
            color: #FDD663;
        }}
        .score-circle.poor {{
            border: 4px solid #F28B82;
            color: #F28B82;
        }}
        .summary-box {{
            background: rgba(138, 180, 248, 0.08);
            border-left: 4px solid #8AB4F8;
            padding: 20px;
            border-radius: 4px;
            margin-bottom: 30px;
            font-size: 15px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
            font-size: 14px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #3C4043;
        }}
        th {{
            background-color: #202124;
            color: #FFFFFF;
        }}
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            font-size: 11px;
            border-radius: 4px;
            font-weight: bold;
        }}
        .badge.numeric {{ background: rgba(138, 180, 248, 0.15); color: #8AB4F8; }}
        .badge.categorical {{ background: rgba(129, 201, 149, 0.15); color: #81C995; }}
        .badge.datetime {{ background: rgba(253, 214, 99, 0.15); color: #FDD663; }}
        .badge.boolean {{ background: rgba(197, 138, 249, 0.15); color: #C58AF9; }}
        .badge.identifier {{ background: rgba(242, 139, 130, 0.15); color: #F28B82; }}
        ul {{
            padding-left: 20px;
        }}
        li {{
            margin-bottom: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>SAAR AI — Executive Analytics Report</h1>
        <div class="meta">
            <strong>Dataset Name:</strong> {filename} | 
            <strong>Date Generated:</strong> {dataset.get('cleaning_history', [{'timestamp': 'Initial analysis'}])[-1].get('timestamp', 'N/A')}
        </div>

        <div class="grid">
            <div class="card">
                <div class="score-circle {color_class}">{score}</div>
                <div class="card-label">Data Quality Score</div>
                <div style="font-size: 11px; margin-top: 5px; color: #9AA0A6;">{explanation}</div>
            </div>
            <div class="card">
                <div class="card-value">{dataset.get('rows_count', 0):,}</div>
                <div class="card-label">Total Records</div>
            </div>
            <div class="card">
                <div class="card-value">{dataset.get('columns_count', 0)}</div>
                <div class="card-label">Total Columns</div>
            </div>
        </div>

        <h2>1. Executive Summary</h2>
        <div class="summary-box">
            {summary}
        </div>

        <h2>2. Technical Quality Observations</h2>
        <ul>
            {"".join(f"<li>{r}</li>" for r in ai_insights.get("quality_score_reasons", []))}
        </ul>

        <h2>3. Attribute Column Profiles</h2>
        <table>
            <thead>
                <tr>
                    <th>Column Name</th>
                    <th>Semantic Type</th>
                    <th>Type</th>
                    <th>Nulls</th>
                    <th>Uniques</th>
                    <th>Key Statistics</th>
                    <th>Outliers</th>
                </tr>
            </thead>
            <tbody>
                {column_table_rows}
            </tbody>
        </table>

        <h2>4. Key Insights</h2>
        <ul>
            {findings_li}
        </ul>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div>
                <h2>5. Business Risks & Warnings</h2>
                <ul style="list-style-type: none; padding-left: 0;">
                    {risks_li}
                </ul>
            </div>
            <div>
                <h2>6. Opportunities & Next Steps</h2>
                <ul style="list-style-type: none; padding-left: 0;">
                    {opp_li}
                </ul>
            </div>
        </div>
    </div>
</body>
</html>
        """
        return html
