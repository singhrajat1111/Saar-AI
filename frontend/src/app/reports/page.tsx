/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useState } from "react";
import { useDatasetStore } from "@/store/use-dataset-store";
import { 
  FileText, 
  Download, 
  ArrowRight, 
  Database, 
  AlertTriangle, 
  Lightbulb, 
  Calendar, 
  History,
  Sparkles
} from "lucide-react";
import Link from "next/link";
import { AIExplainModal } from "@/components/ui/ai-explain-modal";
import { ExportCenterModal } from "@/components/ui/export-center-modal";


export default function ReportsPage() {
  const { datasetId, datasetResults } = useDatasetStore();
  const [modalOpen, setModalOpen] = useState(false);
  const [modalType, setModalType] = useState<any>("report");
  const [modalTitle, setModalTitle] = useState("");
  const [modalPayload, setModalPayload] = useState<any>(null);
  const [exportOpen, setExportOpen] = useState(false);


  if (!datasetId || !datasetResults) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[70vh] text-center p-8">
        <div className="h-16 w-16 bg-muted/30 rounded-2xl flex items-center justify-center mb-6 border border-border">
          <FileText className="h-8 w-8 text-muted-foreground" />
        </div>
        <h2 className="text-2xl font-medium text-foreground mb-2">No Reports Generated</h2>
        <p className="text-muted-foreground max-w-sm mb-6">
          To view and export executive reports, you must first upload a dataset.
        </p>
        <Link href="/" className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors text-sm font-medium">
          Upload Dataset <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    );
  }

  const aiInsights = datasetResults.ai_insights || {};
  const findings = aiInsights.key_findings || [];
  const risks = aiInsights.risks || [];
  const opportunities = aiInsights.opportunities || [];
  const cleaningHistory = datasetResults.cleaning_history || [];

  return (
    <div className="mx-auto max-w-4xl space-y-8 animate-in fade-in duration-500">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-border pb-5 gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-foreground">
            Executive Analytics Report
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Comprehensive business analysis and quality score compiled for <span className="font-semibold text-foreground font-mono">{datasetResults.filename}</span>
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setExportOpen(true)}
            className="px-3.5 py-2 text-xs font-medium rounded-lg border border-border bg-card hover:bg-muted transition-colors inline-flex items-center gap-1.5 shadow-sm cursor-pointer"
          >
            <Download className="h-3.5 w-3.5" /> Export Report
          </button>
          <button
            onClick={() => {
              setModalType("presentation");
              setModalTitle("Executive Presentation Mode");
              setModalPayload({
                filename: datasetResults.filename,
                executive_summary: aiInsights.executive_summary,
                key_findings: findings,
                risks: risks,
                opportunities: opportunities
              });
              setModalOpen(true);
            }}
            className="px-3.5 py-2 text-xs font-medium rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors inline-flex items-center gap-1.5 shadow-sm cursor-pointer"
          >
            <Sparkles className="h-3.5 w-3.5" /> Presentation Mode
          </button>
        </div>
      </div>

      {/* Main Narrative Block */}
      <div className="border border-border bg-card rounded-xl p-6 md:p-8 shadow-sm space-y-6">
        <div className="flex items-center gap-3 border-b border-border/50 pb-4">
          <div className="h-8 w-8 bg-primary/10 rounded-lg flex items-center justify-center">
            <FileText className="h-4.5 w-4.5 text-primary" />
          </div>
          <div>
            <h3 className="text-lg font-medium text-foreground">1. Executive Summary</h3>
            <span className="text-[11px] text-muted-foreground flex items-center gap-1 mt-0.5">
              <Calendar className="h-3.5 w-3.5" /> Analysis Compiled by SAAR Engine
            </span>
          </div>
        </div>

        <p className="text-sm md:text-base text-foreground/90 leading-relaxed font-sans">
          {aiInsights.executive_summary}
        </p>
      </div>

      {/* Key Analytical Findings */}
      <div className="border border-border bg-card rounded-xl p-6 md:p-8 shadow-sm space-y-6">
        <div className="flex items-center gap-3 border-b border-border/50 pb-4">
          <div className="h-8 w-8 bg-primary/10 rounded-lg flex items-center justify-center">
            <Database className="h-4.5 w-4.5 text-primary" />
          </div>
          <h3 className="text-lg font-medium text-foreground">2. Key Findings & Trends</h3>
        </div>

        <div className="space-y-4">
          {findings.map((f: string, i: number) => (
            <div key={i} className="flex items-start gap-3 text-sm text-foreground/90 bg-muted/10 p-3 rounded-lg border border-border/30">
              <span className="font-bold text-primary font-mono shrink-0">{String(i+1).padStart(2, '0')}.</span>
              <p className="leading-relaxed flex-1">{f}</p>
              <button
                onClick={() => {
                  setModalType("insight");
                  setModalTitle(`Explain Finding ${i + 1}`);
                  setModalPayload({ type: "finding", category: "Key Finding", insight: f, finding_index: i + 1 });
                  setModalOpen(true);
                }}
                className="shrink-0 px-2 py-1 text-[10px] font-medium rounded border border-border bg-card text-muted-foreground hover:text-foreground hover:bg-muted transition-all inline-flex items-center gap-1"
              >
                <Sparkles className="h-3 w-3 text-primary" /> Explain
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Risks and Opportunities Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Risks */}
        <div className="border border-border bg-card rounded-xl p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2 border-b border-border/40 pb-3">
            <AlertTriangle className="h-5 w-5 text-rose-400" />
            <h3 className="text-base font-medium text-foreground">Business Risks & Anomalies</h3>
          </div>
          <ul className="text-xs text-muted-foreground space-y-3">
            {risks.map((r: string, i: number) => (
              <li key={i} className="flex items-start gap-2 leading-relaxed bg-rose-500/5 border border-rose-500/10 p-2.5 rounded-lg">
                <span className="text-rose-400 mt-0.5 shrink-0">•</span>
                <span className="text-foreground/90 flex-1">{r}</span>
                <button
                  onClick={() => {
                    setModalType("insight");
                    setModalTitle(`Explain Risk: ${r.substring(0, 40)}...`);
                    setModalPayload({ type: "risk", category: "Business Risk", insight: r });
                    setModalOpen(true);
                  }}
                  className="shrink-0 px-2 py-0.5 text-[10px] font-medium rounded border border-rose-500/20 bg-rose-500/5 text-rose-400 hover:bg-rose-500/10 transition-all inline-flex items-center gap-1"
                >
                  <Sparkles className="h-2.5 w-2.5" /> Explain
                </button>
              </li>
            ))}
          </ul>
        </div>

        {/* Opportunities */}
        <div className="border border-border bg-card rounded-xl p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2 border-b border-border/40 pb-3">
            <Lightbulb className="h-5 w-5 text-emerald-400" />
            <h3 className="text-base font-medium text-foreground">Analytical Opportunities</h3>
          </div>
          <ul className="text-xs text-muted-foreground space-y-3">
            {opportunities.map((opp: string, i: number) => (
              <li key={i} className="flex items-start gap-2 leading-relaxed bg-emerald-500/5 border border-emerald-500/10 p-2.5 rounded-lg">
                <span className="text-emerald-400 mt-0.5 shrink-0">•</span>
                <span className="text-foreground/90 flex-1">{opp}</span>
                <button
                  onClick={() => {
                    setModalType("insight");
                    setModalTitle(`Explain Opportunity`);
                    setModalPayload({ type: "opportunity", category: "Analytical Opportunity", insight: opp });
                    setModalOpen(true);
                  }}
                  className="shrink-0 px-2 py-0.5 text-[10px] font-medium rounded border border-emerald-500/20 bg-emerald-500/5 text-emerald-400 hover:bg-emerald-500/10 transition-all inline-flex items-center gap-1"
                >
                  <Sparkles className="h-2.5 w-2.5" /> Explain
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Applied Cleaning Operations History (if any) */}
      {cleaningHistory.length > 0 && (
        <div className="border border-border bg-card rounded-xl p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2 border-b border-border/40 pb-3">
            <History className="h-5 w-5 text-primary" />
            <h3 className="text-base font-medium text-foreground">Dataset Cleaning History</h3>
          </div>
          <div className="space-y-4">
            {cleaningHistory.map((historyItem: any, i: number) => (
              <div key={i} className="text-xs border border-border/50 rounded-lg p-3 bg-muted/20">
                <div className="flex items-center justify-between mb-2 text-muted-foreground">
                  <span className="font-semibold">Cleaning Phase #{i + 1}</span>
                  <span>{new Date(historyItem.timestamp).toLocaleString()}</span>
                </div>
                <ul className="list-disc pl-4 space-y-1 text-foreground/95">
                  {historyItem.operations.map((op: any, j: number) => (
                    <li key={j} className="font-mono">
                      Applied: <span className="text-primary font-bold">{op.type}</span> 
                      {op.column && <> on column <span className="font-semibold text-yellow-400">'{op.column}'</span></>}
                      {op.strategy && <> (strategy: <span className="italic">{op.strategy}</span>)</>}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      )}
      <AIExplainModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        type={modalType}
        title={modalTitle}
        payload={modalPayload}
      />
      <ExportCenterModal
        isOpen={exportOpen}
        onClose={() => setExportOpen(false)}
        datasetId={datasetId}
        filename={datasetResults.filename}
      />
    </div>
  );
}
