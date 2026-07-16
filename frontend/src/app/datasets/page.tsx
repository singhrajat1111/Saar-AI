/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useEffect, useState } from "react";
import { useDatasetStore } from "@/store/use-dataset-store";
import { 
  Database, 
  Wand2, 
  CheckCircle2, 
  AlertTriangle, 
  RefreshCw, 
  Table, 
  Eye, 
  FileSpreadsheet, 
  ArrowRight,
  Sparkles,
  HelpCircle
} from "lucide-react";
import axios from "axios";
import Link from "next/link";
import { AIExplainModal } from "@/components/ui/ai-explain-modal";
import { apiUrl } from "@/lib/api";

interface PreviewData {
  columns: string[];
  data: Record<string, any>[];
  total_rows: number;
}

export default function DatasetsPage() {
  const { datasetId, datasetResults, setDatasetResults } = useDatasetStore();
  const [previewData, setPreviewData] = useState<PreviewData | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [cleaning, setCleaning] = useState(false);
  const [selectedOps, setSelectedOps] = useState<Record<string, boolean>>({});
  const [cleaningError, setCleaningError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"preview" | "profiles" | "tests">("preview");

  const [modalOpen, setModalOpen] = useState(false);
  const [modalType, setModalType] = useState<any>("recommendation");
  const [modalTitle, setModalTitle] = useState("");
  const [modalPayload, setModalPayload] = useState<any>(null);


  // Fetch preview data when datasetId is loaded or updated
  useEffect(() => {
    if (!datasetId) return;

    const fetchPreview = async () => {
      setLoadingPreview(true);
      try {
        const res = await axios.get(apiUrl(`/api/datasets/${datasetId}/preview`));
        setPreviewData(res.data);
      } catch (err) {
        console.error("Failed to fetch dataset preview", err);
      } finally {
        setLoadingPreview(false);
      }
    };

    fetchPreview();
  }, [datasetId, datasetResults]); // Reload preview if dataset results change (e.g. after cleaning)

  // Initialize selected operations when recommendations load
  useEffect(() => {
    if (!datasetResults || !datasetResults.cleaning_recommendations) return;
    
    const recs = datasetResults.cleaning_recommendations as any[];
    const initialOps: Record<string, boolean> = {};
    recs.forEach((rec) => {
      initialOps[rec.id] = true; // select all by default
    });
    setSelectedOps(initialOps);
  }, [datasetResults]);

  if (!datasetId || !datasetResults) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[70vh] text-center p-8">
        <div className="h-16 w-16 bg-muted/30 rounded-2xl flex items-center justify-center mb-6 border border-border">
          <Database className="h-8 w-8 text-muted-foreground" />
        </div>
        <h2 className="text-2xl font-medium text-foreground mb-2">No Active Dataset</h2>
        <p className="text-muted-foreground max-w-sm mb-6">
          To perform data profiling, cleaning, and visualizations, you must first upload a dataset.
        </p>
        <Link href="/" className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors text-sm font-medium">
          Upload Dataset <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    );
  }

  const recommendations = (datasetResults.cleaning_recommendations as any[]) || [];
  const schema = (datasetResults.schema as any[]) || [];
  const eda = datasetResults.eda || {};
  const aiInsights = datasetResults.ai_insights || {};
  const score = aiInsights.quality_score ?? 100;
  const scoreExplanation = aiInsights.quality_score_explanation || "";
  const scoreReasons = aiInsights.quality_score_reasons || [];

  const handleToggleOp = (id: string) => {
    setSelectedOps((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleApplyCleaning = async () => {
    setCleaning(true);
    setCleaningError(null);

    // Format list of operations based on selected checkboxes
    const opsToApply = recommendations
      .filter((rec) => selectedOps[rec.id])
      .map((rec) => {
        const payloadOp: Record<string, any> = {
          type: rec.type,
          column: rec.column
        };
        if (rec.type === "impute_missing") {
          payloadOp.strategy = rec.default_strategy;
        } else if (rec.type === "drop_columns") {
          payloadOp.columns = rec.columns;
        }
        return payloadOp;
      });

    if (opsToApply.length === 0) {
      setCleaning(false);
      return;
    }

    try {
      const response = await axios.post(
        apiUrl(`/api/datasets/${datasetId}/clean`),
        { operations: opsToApply }
      );
      setDatasetResults(response.data);
    } catch (err: any) {
      console.error(err);
      setCleaningError(err.response?.data?.detail || "Failed to execute data cleaning.");
    } finally {
      setCleaning(false);
    }
  };

  // Helper to determine score color
  const getScoreColor = (s: number) => {
    if (s >= 90) return "text-emerald-400 border-emerald-500/30 bg-emerald-500/5";
    if (s >= 70) return "text-yellow-400 border-yellow-500/30 bg-yellow-500/5";
    return "text-rose-400 border-rose-500/30 bg-rose-500/5";
  };

  return (
    <div className="mx-auto max-w-6xl space-y-8 animate-in fade-in duration-500">
      <div className="flex items-center justify-between border-b border-border pb-5">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-foreground">
            Data Quality & Cleaning
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            File: <code className="text-primary font-mono">{datasetResults.filename}</code> | 
            Records: <span className="font-semibold text-foreground">{(datasetResults.rows_count || 0).toLocaleString()}</span> | 
            Columns: <span className="font-semibold text-foreground">{datasetResults.columns_count || 0}</span>
          </p>
        </div>
        <a 
          href={apiUrl(`/api/datasets/${datasetId}/download`)}
          className="px-4 py-2 text-sm font-medium rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors inline-flex items-center gap-2 shadow-sm"
        >
          <FileSpreadsheet className="h-4 w-4" /> Download Dataset
        </a>
      </div>

      {/* Grid: Quality Score & Cleaning Panel */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Quality Score Card */}
        <div className="md:col-span-1 border border-border bg-card rounded-xl p-6 flex flex-col justify-between shadow-sm">
          <div>
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-4">
              Data Quality Score
            </span>
            <div className="flex items-baseline gap-2 mb-4">
              <span className={`text-6xl font-bold tracking-tight rounded-xl px-4 py-1 border ${getScoreColor(score)}`}>
                {score}
              </span>
              <span className="text-muted-foreground">/100</span>
            </div>
            <p className="text-sm font-medium text-foreground mb-4 leading-relaxed">
              {scoreExplanation}
            </p>
            {scoreReasons.length > 0 && (
              <div className="space-y-2 mt-4 pt-4 border-t border-border/50">
                <span className="text-xs font-semibold text-foreground block">Key Observations:</span>
                <ul className="text-xs text-muted-foreground space-y-1.5 list-disc pl-4">
                  {scoreReasons.map((reason: string, i: number) => (
                    <li key={i}>{reason}</li>
                  ))}
                </ul>
              </div>
            )}
            <button
              onClick={() => {
                setModalType("quality_score");
                setModalTitle("Explain Quality Score");
                setModalPayload({
                  score: score,
                  explanation: scoreExplanation,
                  reasons: scoreReasons
                });
                setModalOpen(true);
              }}
              className="mt-5 w-full px-3 py-1.5 text-xs font-medium rounded-lg border border-border bg-card text-foreground hover:bg-muted transition-colors inline-flex items-center justify-center gap-1 shadow-sm"
            >
              <Sparkles className="h-3.5 w-3.5 text-primary" /> Explain Quality Score
            </button>
          </div>
        </div>

        {/* Cleaning Recommendations */}
        <div className="md:col-span-2 border border-border bg-card rounded-xl p-6 flex flex-col justify-between shadow-sm">
          <div>
            <div className="flex items-center justify-between mb-4 border-b border-border/40 pb-3">
              <div className="flex items-center gap-2">
                <Wand2 className="h-5 w-5 text-primary" />
                <h3 className="text-lg font-medium text-foreground">Cleaning Recommendations</h3>
              </div>
              <span className="text-xs bg-muted px-2.5 py-1 rounded-full border border-border text-muted-foreground font-medium">
                {recommendations.length} Issues Found
              </span>
            </div>

            {recommendations.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground">
                <CheckCircle2 className="h-10 w-10 text-emerald-400 mb-3" />
                <span className="text-sm font-medium text-foreground mb-1">Dataset is Clean</span>
                <span className="text-xs">No missing values, empty columns, or duplicate records detected.</span>
              </div>
            ) : (
              <div className="space-y-4 max-h-[300px] overflow-y-auto pr-2">
                {recommendations.map((rec: any) => (
                  <div key={rec.id} className="flex items-start gap-3 p-3 rounded-lg border border-border/50 bg-muted/10 hover:bg-muted/20 transition-all">
                    <input 
                      type="checkbox"
                      id={rec.id}
                      checked={!!selectedOps[rec.id]}
                      onChange={() => handleToggleOp(rec.id)}
                      className="mt-1 h-4 w-4 rounded border-border text-primary focus:ring-primary/20 accent-primary"
                    />
                    <div className="flex-1">
                      <label htmlFor={rec.id} className="text-sm font-medium text-foreground cursor-pointer flex items-center gap-1.5">
                        {rec.severity === "high" && <AlertTriangle className="h-3.5 w-3.5 text-rose-400" />}
                        {rec.severity === "medium" && <AlertTriangle className="h-3.5 w-3.5 text-yellow-400" />}
                        {rec.issue}
                      </label>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {rec.recommendation}
                      </p>
                    </div>
                    <button
                      onClick={() => {
                        setModalType("recommendation");
                        setModalTitle(`Why this recommendation?`);
                        setModalPayload(rec);
                        setModalOpen(true);
                      }}
                      className="px-2.5 py-1 text-[11px] font-medium rounded-lg border border-border bg-card text-muted-foreground hover:text-foreground hover:bg-muted transition-colors shrink-0 shadow-sm inline-flex items-center gap-1 mt-0.5"
                    >
                      <Sparkles className="h-3 w-3 text-primary" /> Why this recommendation?
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {recommendations.length > 0 && (
            <div className="mt-6 border-t border-border/50 pt-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <span className="text-xs text-muted-foreground">
                Selected: {Object.values(selectedOps).filter(Boolean).length} / {recommendations.length} fixes
              </span>
              <button 
                onClick={handleApplyCleaning}
                disabled={cleaning || Object.values(selectedOps).filter(Boolean).length === 0}
                className="px-4 py-2 text-sm font-medium rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors inline-flex items-center gap-2 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {cleaning ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" /> Applying Fixes...
                  </>
                ) : (
                  <>
                    <Wand2 className="h-4 w-4" /> Clean Dataset
                  </>
                )}
              </button>
            </div>
          )}
          {cleaningError && (
            <p className="text-xs font-medium text-destructive mt-2">{cleaningError}</p>
          )}
        </div>
      </div>

      {/* Dataset Details Tabs (Preview vs Column Registry vs Statistical Tests) */}
      <div className="border border-border bg-card rounded-xl shadow-sm overflow-hidden">
        <div className="flex border-b border-border bg-muted/20 px-4">
          <button 
            onClick={() => setActiveTab("preview")}
            className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors inline-flex items-center gap-2 ${
              activeTab === "preview" 
                ? "border-primary text-primary" 
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Table className="h-4 w-4" /> Data Preview {
              previewData 
                ? (previewData.total_rows > 100 
                  ? `(First 100 of ${previewData.total_rows} Rows)` 
                  : `(${previewData.total_rows} ${previewData.total_rows === 1 ? 'Row' : 'Rows'})`)
                : '(100 Rows)'
            }
          </button>
          <button 
            onClick={() => setActiveTab("profiles")}
            className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors inline-flex items-center gap-2 ${
              activeTab === "profiles" 
                ? "border-primary text-primary" 
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Eye className="h-4 w-4" /> Column Profile Registry
          </button>
          <button 
            onClick={() => setActiveTab("tests")}
            className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors inline-flex items-center gap-2 ${
              activeTab === "tests" 
                ? "border-primary text-primary" 
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Sparkles className="h-4 w-4" /> Statistical Tests
          </button>
        </div>

        <div className="p-6">
          {activeTab === "preview" && (
            <div className="overflow-x-auto">
              {loadingPreview ? (
                <div className="flex items-center justify-center py-20">
                  <RefreshCw className="h-6 w-6 text-primary animate-spin" />
                  <span className="text-sm text-muted-foreground ml-2">Loading preview records...</span>
                </div>
              ) : previewData ? (
                <table className="w-full text-left text-sm border-collapse">
                  <thead>
                    <tr className="bg-muted/40 border-b border-border">
                      <th className="p-3 font-semibold text-muted-foreground text-xs w-16">#</th>
                      {previewData.columns.map((col) => (
                        <th key={col} className="p-3 font-semibold text-foreground text-xs uppercase tracking-wider font-mono">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {previewData.data.map((row, idx) => (
                      <tr key={idx} className="border-b border-border/50 hover:bg-muted/10 transition-colors">
                        <td className="p-3 text-muted-foreground text-xs font-mono">{idx + 1}</td>
                        {previewData.columns.map((col) => (
                          <td key={col} className="p-3 text-foreground/90 font-mono text-xs max-w-xs truncate">
                            {row[col] !== null && row[col] !== undefined ? String(row[col]) : (
                              <span className="text-destructive/40 italic font-sans">null</span>
                            )}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="py-20 text-center text-muted-foreground text-sm">
                  Failed to load preview. Please refresh or check backend connection.
                </div>
              )}
            </div>
          )}

          {activeTab === "profiles" && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="bg-muted/40 border-b border-border">
                    <th className="p-3 text-muted-foreground text-xs uppercase font-semibold">Column Name</th>
                    <th className="p-3 text-muted-foreground text-xs uppercase font-semibold">Semantic Type</th>
                    <th className="p-3 text-muted-foreground text-xs uppercase font-semibold">Pandas Type</th>
                    <th className="p-3 text-muted-foreground text-xs uppercase font-semibold">Missing Rate</th>
                    <th className="p-3 text-muted-foreground text-xs uppercase font-semibold">Unique Ratio</th>
                    <th className="p-3 text-muted-foreground text-xs uppercase font-semibold">Descriptive Summary</th>
                    <th className="p-3 text-muted-foreground text-xs uppercase font-semibold">Outliers</th>
                  </tr>
                </thead>
                <tbody>
                  {schema.map((col: any) => {
                    const cname = col.column_name;
                    const stype = col.semantic_type;
                    const ptype = col.pandas_dtype;
                    const nullPct = col.null_percentage;
                    const nullCount = col.null_count;
                    const uniqueCount = col.unique_values;
                    const uniqueRatio = ((uniqueCount / (datasetResults.rows_count || 1)) * 100).toFixed(1);

                    // Grab statistics summary
                    let statsSummary = "N/A";
                    let outlierSummary = "N/A";
                    
                    const numStats = eda.numeric_stats || {};
                    const catStats = eda.categorical_stats || {};

                    if (stype === "numeric" && numStats[cname]) {
                      const ns = numStats[cname];
                      statsSummary = `Mean: ${ns.mean?.toFixed(2)} | Median: ${ns.median?.toFixed(2)}`;
                      outlierSummary = `${ns.outliers_count} (${ns.outliers_pct}%)`;
                    } else if ((stype === "categorical" || stype === "boolean") && catStats[cname]) {
                      const cs = catStats[cname];
                      const top = cs.top_categories?.[0];
                      if (top) {
                        statsSummary = `Mode: '${top.value}' (${top.percentage}%)`;
                      }
                    }

                    return (
                      <tr key={cname} className="border-b border-border/50 hover:bg-muted/10 transition-colors">
                        <td className="p-3 font-semibold text-foreground font-mono">{cname}</td>
                        <td className="p-3">
                          <span className={`px-2 py-0.5 text-[11px] font-bold rounded uppercase tracking-wider ${
                            stype === "numeric" ? "bg-blue-500/10 text-blue-400 border border-blue-500/20" :
                            stype === "categorical" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" :
                            stype === "datetime" ? "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20" :
                            stype === "boolean" ? "bg-purple-500/10 text-purple-400 border border-purple-500/20" :
                            "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                          }`}>
                            {stype}
                          </span>
                        </td>
                        <td className="p-3 font-mono text-muted-foreground text-xs"><code>{ptype}</code></td>
                        <td className="p-3">
                          <span className={nullPct > 20 ? "text-rose-400 font-medium" : "text-foreground"}>
                            {nullPct}%
                          </span>
                          <span className="text-xs text-muted-foreground block">({nullCount} rows)</span>
                        </td>
                        <td className="p-3 text-foreground/90">
                          {uniqueRatio}%
                          <span className="text-xs text-muted-foreground block">({uniqueCount} unique)</span>
                        </td>
                        <td className="p-3 text-muted-foreground text-xs font-mono">{statsSummary}</td>
                        <td className="p-3">
                          {outlierSummary !== "N/A" && parseInt(outlierSummary) > 0 ? (
                            <span className="text-yellow-400 font-medium font-mono">{outlierSummary}</span>
                          ) : (
                            <span className="text-muted-foreground font-mono">{outlierSummary}</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === "tests" && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="bg-muted/40 border-b border-border">
                    <th className="p-3 text-muted-foreground text-xs uppercase font-semibold">Test Name</th>
                    <th className="p-3 text-muted-foreground text-xs uppercase font-semibold">Test Type</th>
                    <th className="p-3 text-muted-foreground text-xs uppercase font-semibold">Variables</th>
                    <th className="p-3 text-muted-foreground text-xs uppercase font-semibold">Statistic</th>
                    <th className="p-3 text-muted-foreground text-xs uppercase font-semibold">P-Value</th>
                    <th className="p-3 text-muted-foreground text-xs uppercase font-semibold">Significance</th>
                    <th className="p-3 text-muted-foreground text-xs uppercase font-semibold">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {(() => {
                    const hypothesisTests = (datasetResults.eda?.hypothesis_tests as any[]) || [];
                    const numericStats = datasetResults.eda?.numeric_stats || {};
                    
                    // Extract normality tests from the numeric profile columns
                    const normalityTests = Object.entries(numericStats)
                      .filter(([col, stats]: [string, any]) => stats.normality)
                      .map(([col, stats]: [string, any]) => ({
                        test_type: "Normality Test",
                        test_name: `Shapiro-Wilk Normality Test on '${col}'`,
                        variables: [col],
                        statistic: stats.normality.stat,
                        p_value: stats.normality.p_value,
                        significant: !stats.normality.is_normal,
                        interpretation: stats.normality.is_normal
                          ? `The distribution of '${col}' is normally distributed (p >= 0.05).`
                          : `The distribution of '${col}' deviates significantly from normal (p < 0.05).`
                      }));

                    const allTests = [...normalityTests, ...hypothesisTests];

                    if (allTests.length === 0) {
                      return (
                        <tr>
                          <td colSpan={7} className="p-8 text-center text-muted-foreground italic">
                            No statistical hypothesis tests could be performed on this dataset.
                          </td>
                        </tr>
                      );
                    }

                    return allTests.map((t: any, i: number) => (
                      <tr key={i} className="border-b border-border/50 hover:bg-muted/10 transition-colors">
                        <td className="p-3 font-semibold text-foreground font-mono">{t.test_name}</td>
                        <td className="p-3">
                          <span className="px-2 py-0.5 text-[11px] font-bold rounded uppercase tracking-wider bg-purple-500/10 text-purple-400 border border-purple-500/20">
                            {t.test_type}
                          </span>
                        </td>
                        <td className="p-3 font-mono text-muted-foreground text-xs">{t.variables.join(", ")}</td>
                        <td className="p-3 font-mono text-xs">{t.statistic !== undefined && t.statistic !== null ? t.statistic.toFixed(4) : "N/A"}</td>
                        <td className="p-3 font-mono text-xs">{t.p_value !== undefined && t.p_value !== null ? t.p_value.toFixed(4) : "N/A"}</td>
                        <td className="p-3">
                          {t.significant ? (
                            <span className="px-2.5 py-0.5 text-[10px] font-bold rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20">
                              {"Significant (p < 0.05)"}
                            </span>
                          ) : (
                            <span className="px-2.5 py-0.5 text-[10px] font-bold rounded-full bg-muted border border-border text-muted-foreground">
                              Not Significant
                            </span>
                          )}
                        </td>
                        <td className="p-3">
                          <button
                            onClick={() => {
                              setModalType("statistical_test");
                              setModalTitle(`Explain Result: ${t.test_type}`);
                              setModalPayload(t);
                              setModalOpen(true);
                            }}
                            className="px-2.5 py-1 text-xs font-medium rounded-lg border border-border bg-card text-foreground hover:bg-muted transition-all inline-flex items-center gap-1 shadow-sm"
                          >
                            <Sparkles className="h-3 w-3 text-primary" /> Explain Result
                          </button>
                        </td>
                      </tr>
                    ));
                  })()}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
      <AIExplainModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        type={modalType}
        title={modalTitle}
        payload={modalPayload}
      />
    </div>
  );
}
