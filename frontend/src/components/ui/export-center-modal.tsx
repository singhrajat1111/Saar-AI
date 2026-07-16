"use client";

import { useEffect, useState } from "react";
import {
  X, 
  Code, 
  FileText, 
  FileJson, 
  Download, 
  Sparkles, 
  Info,
  CheckCircle,
  AlertCircle
} from "lucide-react";
import axios from "axios";
import { apiUrl } from "@/lib/api";

interface ExportCenterModalProps {
  isOpen: boolean;
  onClose: () => void;
  datasetId: string;
  filename: string;
}

export function ExportCenterModal({ isOpen, onClose, datasetId, filename }: ExportCenterModalProps) {
  const [format, setFormat] = useState<"html" | "pdf" | "markdown" | "json" | "clean">("html");
  const [reportType, setReportType] = useState<"technical" | "executive">("technical");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewName, setPreviewName] = useState("");

  const baseName = filename ? filename.split(".")[0] : "dataset";

  // Auto-generate preview filename based on options
  useEffect(() => {
    const now = new Date();
    const pad = (n: number) => String(n).padStart(2, "0");
    const dateStr = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
    const timeStr = `${pad(now.getHours())}-${pad(now.getMinutes())}`;
    const cleanBase = baseName.replace(/\s+/g, "_").replace(/,/g, "");
    
    if (format === "clean") {
      const ext = filename.split(".").pop() || "csv";
      setPreviewName(`${cleanBase}_cleaned.${ext}`);
    } else if (format === "json") {
      setPreviewName(`${cleanBase}_Report_${dateStr}_${timeStr}.json`);
    } else {
      const rtype = reportType === "technical" ? "Technical" : "Executive";
      const ext = format === "markdown" ? "md" : format;
      setPreviewName(`${cleanBase}_${rtype}_Report_${dateStr}_${timeStr}.${ext}`);
    }
  }, [format, reportType, baseName, filename]);

  // Handle escape key to close
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleExport = async () => {
    setLoading(true);
    setError(null);
    try {
      if (format === "clean") {
        // Direct file download for clean dataset
        window.location.href = apiUrl(`/api/datasets/${datasetId}/download`);
        setTimeout(() => {
          setLoading(false);
          onClose();
        }, 1000);
        return;
      }

      // Download file programmatically via link element
      const response = await axios({
        url: apiUrl(`/api/datasets/${datasetId}/report`),
        method: "GET",
        params: {
          format,
          report_type: reportType
        },
        responseType: "blob"
      });

      const blob = new Blob([response.data], { type: (response.headers["content-type"] as string) || undefined });
      const link = document.createElement("a");
      link.href = window.URL.createObjectURL(blob);
      link.download = previewName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      setLoading(false);
      onClose();
    } catch (err: any) {
      console.error("Export failed:", err);
      setError("Failed to generate and download report. Please check if backend is running.");
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-2xl bg-card border border-border rounded-xl shadow-lg overflow-hidden animate-slide-up flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <div className="flex items-center gap-2">
            <div className="h-9 w-9 bg-primary/10 rounded-lg flex items-center justify-center">
              <Download className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-foreground">Export Center</h2>
              <p className="text-xs text-muted-foreground">Download reports or cleaned datasets</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-1 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors cursor-pointer"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Format selection */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider">1. Select Format</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {/* HTML */}
              <button
                onClick={() => setFormat("html")}
                className={`flex flex-col items-start p-4 rounded-xl border text-left transition-all cursor-pointer ${
                  format === "html" 
                    ? "border-primary bg-primary/5 shadow-sm" 
                    : "border-border hover:border-foreground/20 bg-card"
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <div className={`p-1.5 rounded-lg ${format === "html" ? "bg-primary/20 text-primary" : "bg-muted text-muted-foreground"}`}>
                    <Code className="h-4 w-4" />
                  </div>
                  <span className="font-semibold text-sm text-foreground">HTML</span>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Interactive, responsive and visually stunning. Best for presentation in browsers.
                </p>
              </button>

              {/* PDF */}
              <button
                onClick={() => setFormat("pdf")}
                className={`flex flex-col items-start p-4 rounded-xl border text-left transition-all cursor-pointer ${
                  format === "pdf" 
                    ? "border-primary bg-primary/5 shadow-sm" 
                    : "border-border hover:border-foreground/20 bg-card"
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <div className={`p-1.5 rounded-lg ${format === "pdf" ? "bg-primary/20 text-primary" : "bg-muted text-muted-foreground"}`}>
                    <FileText className="h-4 w-4" />
                  </div>
                  <span className="font-semibold text-sm text-foreground">PDF</span>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Professional printable report with pagination, cover page, headers & footers.
                </p>
              </button>

              {/* Markdown */}
              <button
                onClick={() => setFormat("markdown")}
                className={`flex flex-col items-start p-4 rounded-xl border text-left transition-all cursor-pointer ${
                  format === "markdown" 
                    ? "border-primary bg-primary/5 shadow-sm" 
                    : "border-border hover:border-foreground/20 bg-card"
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <div className={`p-1.5 rounded-lg ${format === "markdown" ? "bg-primary/20 text-primary" : "bg-muted text-muted-foreground"}`}>
                    <FileText className="h-4 w-4" />
                  </div>
                  <span className="font-semibold text-sm text-foreground">Markdown</span>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Developer-friendly, perfect for GitHub README documentation or notes.
                </p>
              </button>

              {/* JSON */}
              <button
                onClick={() => setFormat("json")}
                className={`flex flex-col items-start p-4 rounded-xl border text-left transition-all cursor-pointer ${
                  format === "json" 
                    ? "border-primary bg-primary/5 shadow-sm" 
                    : "border-border hover:border-foreground/20 bg-card"
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <div className={`p-1.5 rounded-lg ${format === "json" ? "bg-primary/20 text-primary" : "bg-muted text-muted-foreground"}`}>
                    <FileJson className="h-4 w-4" />
                  </div>
                  <span className="font-semibold text-sm text-foreground">JSON Data</span>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Full computed statistics, schema, and insights. Best for API ingestion.
                </p>
              </button>

              {/* Clean Dataset */}
              <button
                onClick={() => setFormat("clean")}
                className={`flex flex-col items-start p-4 rounded-xl border text-left transition-all cursor-pointer md:col-span-2 ${
                  format === "clean" 
                    ? "border-primary bg-primary/5 shadow-sm" 
                    : "border-border hover:border-foreground/20 bg-card"
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <div className={`p-1.5 rounded-lg ${format === "clean" ? "bg-primary/20 text-primary" : "bg-muted text-muted-foreground"}`}>
                    <CheckCircle className="h-4 w-4" />
                  </div>
                  <span className="font-semibold text-sm text-foreground">Clean Dataset</span>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Download the dataset file after applying all cleaning, deduplication, and imputations.
                </p>
              </button>
            </div>
          </div>

          {/* Report Type (if not downloading clean dataset/json) */}
          {format !== "clean" && format !== "json" && (
            <div className="space-y-3 pt-2">
              <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider">2. Select Report Type</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Technical */}
                <button
                  onClick={() => setReportType("technical")}
                  className={`flex flex-col items-start p-4 rounded-xl border text-left transition-all cursor-pointer ${
                    reportType === "technical" 
                      ? "border-primary bg-primary/5 shadow-sm" 
                      : "border-border hover:border-foreground/20 bg-card"
                  }`}
                >
                  <span className="font-semibold text-sm text-foreground mb-1">Technical Report</span>
                  <span className="text-xs text-muted-foreground leading-relaxed">
                    Designed for developers, researchers, and data analysts. Includes full column registry, statistical distribution summaries, hypothesis tests, and modeling details.
                  </span>
                </button>

                {/* Executive */}
                <button
                  onClick={() => setReportType("executive")}
                  className={`flex flex-col items-start p-4 rounded-xl border text-left transition-all cursor-pointer ${
                    reportType === "executive" 
                      ? "border-primary bg-primary/5 shadow-sm" 
                      : "border-border hover:border-foreground/20 bg-card"
                  }`}
                >
                  <span className="font-semibold text-sm text-foreground mb-1 font-sans">Executive Report</span>
                  <span className="text-xs text-muted-foreground leading-relaxed">
                    Designed for business managers, clients, and decision-makers. Focuses on high-level insights, health overview, risks, recommendations, and next steps.
                  </span>
                </button>
              </div>
            </div>
          )}

          {/* Filename Preview */}
          <div className="bg-muted/30 border border-border/50 rounded-xl p-4 space-y-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground block">
              Filename Preview
            </span>
            <div className="flex items-center gap-2 text-xs font-mono text-foreground break-all">
              <FileText className="h-4 w-4 text-primary shrink-0" />
              <span>{previewName}</span>
            </div>
          </div>

          {/* Methodology Info Card */}
          {format !== "clean" && (
            <div className="bg-primary/5 border border-primary/10 rounded-xl p-4 flex gap-3 text-xs leading-relaxed text-muted-foreground">
              <Info className="h-5 w-5 text-primary shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-foreground block mb-0.5">Methodology Disclaimer</span>
                This report is compiled directly from the statistical computations of the Python Statistical Engine. 
                AI did not modify any analytical figures.
              </div>
            </div>
          )}

          {error && (
            <div className="bg-destructive/10 border border-destructive/20 rounded-xl p-4 flex gap-3 text-xs leading-relaxed text-destructive">
              <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
              <div>{error}</div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-border flex items-center justify-between bg-muted/10 gap-4">
          <span className="text-xs text-muted-foreground hidden sm:inline">
            Subtle transparent branding applied to footers
          </span>
          <div className="flex gap-3 w-full sm:w-auto">
            <button
              onClick={onClose}
              className="flex-1 sm:flex-initial px-4 py-2 text-sm font-medium rounded-lg border border-border text-foreground hover:bg-muted transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              onClick={handleExport}
              disabled={loading}
              className="flex-1 sm:flex-initial px-4 py-2 text-sm font-medium rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors inline-flex items-center justify-center gap-2 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              {loading ? (
                <>
                  <div className="h-4 w-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  Export File
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
