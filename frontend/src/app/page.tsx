/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useState } from "react";
import { useDatasetStore } from "@/store/use-dataset-store";
import { UploadZone } from "@/features/datasets/components/upload-zone";
import { LiveTimeline } from "@/features/dashboard/components/live-timeline";
import { BarChart3, Database, FileText, BrainCircuit, ArrowRight } from "lucide-react";
import Link from "next/link";
import { AIExplainModal } from "@/components/ui/ai-explain-modal";

export default function DashboardPage() {
  const { isUploading, datasetResults, reset, datasetId } = useDatasetStore();
  const [modalOpen, setModalOpen] = useState(false);
  const [modalType, setModalType] = useState<any>("executive_summary");
  const [modalTitle, setModalTitle] = useState("");
  const [modalPayload, setModalPayload] = useState<any>(null);


  if (datasetResults) {
    // Executive Dashboard View
    const eda = datasetResults.eda || {};
    const quality = eda.quality || {};
    const totalRows = quality.total_rows || 0;
    const duplicateRows = quality.duplicate_rows || 0;
    const missingValues = quality.missing_values || {};
    const totalMissing = Object.values(missingValues).reduce((a: any, b: any) => (a as number) + (b as number), 0) as number;
    
    const mlRecs = datasetResults.ml_recommendations || {};
    const potentialTargets = mlRecs.potential_targets || [];
    const features = mlRecs.potential_features || [];

    const aiInsights = datasetResults.ai_insights || {};
    const executiveSummary = aiInsights.executive_summary || "No summary available.";
    const keyFindings = aiInsights.key_findings || [];

    return (
      <div className="mx-auto max-w-5xl py-8 space-y-8 animate-in fade-in duration-500">
        <div className="flex items-center justify-between border-b border-border pb-5">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-foreground">
              Executive Analytics Dashboard
            </h1>
            <p className="text-sm text-muted-foreground mt-1 font-mono">
              Dataset: <span className="text-primary">{datasetResults.filename}</span>
            </p>
          </div>
          <div className="flex gap-2">
            <Link 
              href="/reports" 
              className="px-4 py-2 text-sm font-medium rounded-lg border border-border bg-card hover:bg-muted transition-colors inline-flex items-center gap-1.5 shadow-sm"
            >
              <FileText className="h-4 w-4" /> View Full Report
            </Link>
            <button 
              onClick={reset}
              className="px-4 py-2 text-sm font-medium rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors shadow-sm"
            >
              Analyze New
            </button>
          </div>
        </div>

        {/* Executive Summary */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center justify-between border-b border-border/40 pb-3 mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <FileText className="h-5 w-5 text-primary" />
              </div>
              <h2 className="text-xl font-medium text-foreground">Executive Summary</h2>
            </div>
            <button 
              onClick={() => {
                setModalType("executive_summary");
                setModalTitle("Regenerate Executive Summary");
                setModalPayload({
                  quality: quality,
                  total_rows: totalRows,
                  duplicate_rows: duplicateRows,
                  missing_values: missingValues,
                  potential_targets: potentialTargets,
                  potential_features: features
                });
                setModalOpen(true);
              }}
              className="px-3 py-1.5 text-xs font-medium rounded-lg border border-border bg-card text-foreground hover:bg-muted transition-colors inline-flex items-center gap-1 shadow-sm"
            >
              <BrainCircuit className="h-3.5 w-3.5 text-primary" /> Regenerate Summary
            </button>
          </div>
          <p className="text-sm md:text-base text-foreground/90 leading-relaxed font-sans">
            {executiveSummary}
          </p>
        </div>

        {/* Quick Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            { label: "Total Records", value: totalRows, icon: Database },
            { label: "Missing Values", value: totalMissing, icon: BarChart3 },
            { label: "Duplicates", value: duplicateRows, icon: FileText },
            { label: "Inferred Features", value: features.length, icon: BrainCircuit },
          ].map((stat, i) => (
            <div key={i} className="rounded-xl border border-border bg-card p-5 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm font-medium text-muted-foreground">{stat.label}</span>
                <stat.icon className="h-4 w-4 text-muted-foreground" />
              </div>
              <span className="text-2xl font-semibold text-foreground font-mono">
                {typeof stat.value === 'number' ? stat.value.toLocaleString() : stat.value}
              </span>
            </div>
          ))}
        </div>

        {/* Two Column Layout for Insights and ML */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Key Findings Preview */}
          <div className="rounded-xl border border-border bg-card p-6 shadow-sm flex flex-col justify-between">
            <div>
              <h3 className="text-lg font-medium text-foreground mb-4">Key Findings</h3>
              <ul className="space-y-3">
                {keyFindings.slice(0, 4).map((finding: string, i: number) => (
                  <li key={i} className="text-sm text-muted-foreground flex gap-2">
                    <span className="text-primary mt-0.5">•</span> 
                    <span className="text-foreground/90">{finding}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="mt-6 pt-4 border-t border-border/50">
              <Link href="/reports" className="text-sm text-primary hover:underline inline-flex items-center gap-1.5 font-medium">
                View all insights and risks <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
          
          {/* ML Recommendations Preview */}
          <div className="rounded-xl border border-border bg-card p-6 shadow-sm flex flex-col justify-between">
            <div>
              <h3 className="text-lg font-medium text-foreground mb-4">Modeling Recommendations</h3>
              {potentialTargets.length === 0 ? (
                <p className="text-sm text-muted-foreground italic">
                  No obvious regression or classification targets identified. Consider clustering or dimensionality reduction.
                </p>
              ) : (
                <div className="space-y-3">
                  {potentialTargets.slice(0, 2).map((rec: Record<string, any>, i: number) => (
                    <div key={i} className="p-3.5 rounded-lg bg-muted/30 border border-border/50">
                      <span className="text-[10px] font-bold text-primary uppercase tracking-wider mb-1 block">
                        {rec.task}
                      </span>
                      <p className="text-sm font-semibold text-foreground mb-2">Target: <code>{rec.column}</code></p>
                      <div className="flex flex-wrap gap-1.5">
                        {rec.suggested_models.map((model: string, j: number) => (
                          <span key={j} className="px-2 py-0.5 text-[10px] rounded-md bg-background border border-border text-muted-foreground">
                            {model}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="mt-6 pt-4 border-t border-border/50">
              <Link href="/visualize" className="text-sm text-primary hover:underline inline-flex items-center gap-1.5 font-medium">
                Explore recommended visual charts <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
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

  return (
    <div className="mx-auto max-w-3xl py-10 animate-in fade-in duration-500">
      <div className="mb-10 text-center">
        <img 
          src="/logo.svg" 
          alt="SAAR Logo" 
          className="mx-auto h-24 mb-6 object-contain filter drop-shadow-[0_0_20px_rgba(26,115,232,0.25)] select-none"
        />
        <h1 className="text-4xl font-semibold tracking-tight text-foreground mb-4">
          Discover the Essence of Your Data
        </h1>
        <p className="text-lg text-muted-foreground max-w-xl mx-auto">
          Upload any dataset. SAAR AI will automatically clean it, analyze the statistics, and generate an executive report.
        </p>
      </div>

      {!isUploading ? <UploadZone /> : <LiveTimeline />}
    </div>
  );
}
