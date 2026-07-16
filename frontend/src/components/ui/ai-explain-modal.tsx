"use client";

import { useEffect, useState, useCallback } from "react";
import {
  X,
  Sparkles,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
  FlaskConical,
} from "lucide-react";
import axios from "axios";
import { useDatasetStore } from "@/store/use-dataset-store";
import { apiUrl } from "@/lib/api";

// ── Types ─────────────────────────────────────────────────────────────────────

interface EvidenceItem {
  label: string;
  value: string;
  source: string;
}

interface StructuredExplanation {
  title: string;
  summary: string;
  key_takeaway: string;
  evidence: EvidenceItem[];
  limitations: string;
  provider: string;
  generated_at: string;
  cached?: boolean;
}

interface AIExplainModalProps {
  isOpen: boolean;
  onClose: () => void;
  type:
    | "recommendation"
    | "chart"
    | "statistical_test"
    | "executive_summary"
    | "quality_score"
    | "insight"
    | "report"
    | "presentation";
  title: string;
  payload: any;
}

// ── Skeleton loader ───────────────────────────────────────────────────────────

function SkeletonLoader() {
  return (
    <div className="space-y-5 animate-pulse py-2">
      {/* Title skeleton */}
      <div className="h-4 bg-muted/60 rounded-lg w-2/3" />
      {/* Summary lines */}
      <div className="space-y-2.5">
        <div className="h-3.5 bg-muted/50 rounded w-full" />
        <div className="h-3.5 bg-muted/50 rounded w-full" />
        <div className="h-3.5 bg-muted/50 rounded w-5/6" />
        <div className="h-3.5 bg-muted/50 rounded w-4/5" />
        <div className="h-3.5 bg-muted/40 rounded w-3/4" />
      </div>
      {/* Key takeaway skeleton */}
      <div className="h-16 bg-primary/5 border border-primary/10 rounded-xl" />
      {/* Evidence skeleton */}
      <div className="space-y-2 mt-4">
        <div className="h-3 bg-muted/40 rounded w-1/3" />
        <div className="h-8 bg-muted/30 rounded-lg w-full" />
        <div className="h-8 bg-muted/30 rounded-lg w-full" />
      </div>
    </div>
  );
}

// ── Copy button ───────────────────────────────────────────────────────────────

function CopyButton({ text, label }: { text: string; label: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard not available */
    }
  }, [text]);

  return (
    <button
      onClick={handleCopy}
      className="inline-flex items-center gap-1 px-2 py-1 text-[11px] font-medium rounded-md border border-border bg-card text-muted-foreground hover:text-foreground hover:bg-muted transition-all"
      title={`Copy ${label}`}
    >
      {copied ? (
        <Check className="h-3 w-3 text-emerald-400" />
      ) : (
        <Copy className="h-3 w-3" />
      )}
      {copied ? "Copied" : `Copy ${label}`}
    </button>
  );
}

// ── Main modal ────────────────────────────────────────────────────────────────

export function AIExplainModal({
  isOpen,
  onClose,
  type,
  title,
  payload,
}: AIExplainModalProps) {
  const [level, setLevel] = useState<"beginner" | "intermediate" | "expert">(
    "intermediate"
  );
  const [explanation, setExplanation] = useState<StructuredExplanation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showEvidence, setShowEvidence] = useState(false);
  const { datasetId } = useDatasetStore();

  useEffect(() => {
    if (!isOpen || !payload) return;
    let cancelled = false;

    const fetchExplanation = async () => {
      setLoading(true);
      setError(null);
      setExplanation(null);
      setShowEvidence(false);
      try {
        const response = await axios.post(apiUrl("/api/ai/explain"), {
          type,
          level,
          payload,
          dataset_id: datasetId,
        });
        if (!cancelled) {
          setExplanation(response.data as StructuredExplanation);
        }
      } catch (err: any) {
        if (!cancelled) {
          setError(
            err.response?.data?.detail ||
              "Failed to generate explanation. Please try again."
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchExplanation();
    return () => {
      cancelled = true;
    };
  }, [isOpen, type, level, payload]);

  // Reset state on close
  useEffect(() => {
    if (!isOpen) {
      setExplanation(null);
      setError(null);
      setLoading(false);
      setShowEvidence(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const providerBadge =
    explanation?.provider === "gemini"
      ? "Gemini"
      : explanation?.provider === "openai"
      ? "OpenAI"
      : explanation?.cached
      ? "Cached"
      : explanation?.provider === "rule_based_fallback"
      ? "Local Engine"
      : null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-end">
      {/* Backdrop */}
      <div
        onClick={onClose}
        className="absolute inset-0 bg-background/75 backdrop-blur-sm transition-opacity duration-200"
      />

      {/* Drawer Panel */}
      <div
        className="relative w-full max-w-lg h-full bg-card border-l border-border flex flex-col shadow-2xl"
        style={{ animation: "slideInRight 0.25s cubic-bezier(0.16, 1, 0.3, 1)" }}
      >
        {/* ── Header ── */}
        <div className="flex items-start justify-between border-b border-border px-6 py-4 bg-muted/20 shrink-0">
          <div className="flex-1 mr-4">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[11px] font-semibold bg-primary/10 text-primary border border-primary/20 rounded-full px-2.5 py-0.5 inline-flex items-center gap-1">
                <Sparkles className="h-3 w-3" /> Enhanced with AI
              </span>
              {providerBadge && (
                <span className="text-[10px] font-mono text-muted-foreground bg-muted/50 border border-border px-2 py-0.5 rounded-full">
                  via {providerBadge}
                </span>
              )}
            </div>
            <h3
              className="text-base font-semibold text-foreground mt-2 leading-snug"
              title={title}
            >
              {title}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg border border-border bg-card text-muted-foreground hover:text-foreground hover:bg-muted transition-all shrink-0"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* ── Level Controls ── */}
        <div className="border-b border-border bg-muted/10 px-6 py-3 flex items-center justify-between gap-3 shrink-0">
          <span className="text-xs font-medium text-muted-foreground">
            Explanation Level
          </span>
          <div className="inline-flex rounded-lg border border-border bg-card p-0.5">
            {(["beginner", "intermediate", "expert"] as const).map((lvl) => (
              <button
                key={lvl}
                onClick={() => setLevel(lvl)}
                className={`px-3 py-1 text-xs font-medium rounded-md capitalize transition-all ${
                  level === lvl
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>
        </div>

        {/* ── Content ── */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">
          {loading ? (
            <SkeletonLoader />
          ) : error ? (
            <div className="flex gap-3 p-4 rounded-xl border border-rose-500/20 bg-rose-500/5 text-rose-400">
              <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-semibold">Explanation Error</h4>
                <p className="text-xs text-rose-400/90 mt-1 leading-relaxed">
                  {error}
                </p>
              </div>
            </div>
          ) : explanation ? (
            <>
              {/* Explanation title */}
              {explanation.title && (
                <h4 className="text-sm font-bold text-foreground tracking-tight">
                  {explanation.title}
                </h4>
              )}

              {/* Summary with copy button */}
              {explanation.summary && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                      Explanation
                    </span>
                    <CopyButton text={explanation.summary} label="Explanation" />
                  </div>
                  <div className="text-sm text-foreground/90 leading-relaxed space-y-2 font-sans">
                    {explanation.summary.split("\n").map((line, i) => {
                      const t = line.trim();
                      if (!t) return <div key={i} className="h-1" />;
                      if (t.startsWith("- ") || t.startsWith("• ")) {
                        return (
                          <p key={i} className="flex gap-2">
                            <span className="text-primary mt-1 shrink-0">•</span>
                            <span>{t.replace(/^[-•]\s*/, "")}</span>
                          </p>
                        );
                      }
                      return <p key={i}>{line}</p>;
                    })}
                  </div>
                </div>
              )}

              {/* Key Takeaway */}
              {explanation.key_takeaway && (
                <div className="rounded-xl border border-primary/20 bg-primary/5 p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-semibold text-primary uppercase tracking-wider flex items-center gap-1">
                      <Sparkles className="h-3 w-3" /> Key Takeaway
                    </span>
                    <CopyButton
                      text={explanation.key_takeaway}
                      label="Takeaway"
                    />
                  </div>
                  <p className="text-sm font-medium text-foreground leading-relaxed">
                    {explanation.key_takeaway}
                  </p>
                </div>
              )}

              {/* Limitations */}
              {explanation.limitations &&
                explanation.limitations.toLowerCase() !== "none" && (
                  <p className="text-[11px] text-muted-foreground italic leading-relaxed border-l-2 border-border pl-3">
                    {explanation.limitations}
                  </p>
                )}

              {/* Supporting Evidence Collapsible */}
              {explanation.evidence && explanation.evidence.length > 0 && (
                <div className="border-t border-border/50 pt-4">
                  <button
                    onClick={() => setShowEvidence(!showEvidence)}
                    className="flex items-center justify-between w-full text-left text-xs font-medium text-muted-foreground hover:text-foreground transition-colors group"
                  >
                    <span className="flex items-center gap-1.5">
                      <FlaskConical className="h-3.5 w-3.5" />
                      View Supporting Evidence
                      <span className="ml-1 px-1.5 py-0.5 bg-muted rounded-full text-[10px]">
                        {explanation.evidence.length}
                      </span>
                    </span>
                    {showEvidence ? (
                      <ChevronUp className="h-4 w-4 text-muted-foreground group-hover:text-foreground" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-muted-foreground group-hover:text-foreground" />
                    )}
                  </button>

                  {showEvidence && (
                    <div
                      className="mt-3 space-y-2"
                      style={{ animation: "fadeIn 0.15s ease" }}
                    >
                      <p className="text-[11px] text-muted-foreground leading-relaxed mb-3">
                        These values were computed locally by the{" "}
                        <span className="font-semibold text-foreground">
                          Python Statistical Engine
                        </span>{" "}
                        and are the sole basis for the explanation above.
                      </p>
                      <div className="rounded-xl border border-border/60 overflow-hidden bg-muted/10">
                        {explanation.evidence.map((item, i) => (
                          <div
                            key={i}
                            className="flex items-start justify-between gap-4 px-4 py-2.5 border-b border-border/30 last:border-b-0 hover:bg-muted/20 transition-colors"
                          >
                            <span className="text-xs text-muted-foreground font-mono flex-1 truncate">
                              {item.label}
                            </span>
                            <span className="text-xs font-semibold text-foreground font-mono text-right select-all max-w-[55%] break-words">
                              {item.value}
                            </span>
                          </div>
                        ))}
                      </div>
                      <p className="text-[10px] text-muted-foreground/60 text-right font-mono">
                        Source: Python Statistical Engine
                      </p>
                    </div>
                  )}
                </div>
              )}
            </>
          ) : null}
        </div>

        {/* ── Footer ── */}
        <div className="border-t border-border px-6 py-3.5 bg-muted/20 shrink-0">
          <p className="text-[10px] text-muted-foreground leading-relaxed text-center">
            This explanation is based entirely on verified statistical analysis generated by{" "}
            SAAR&apos;s Python Statistical Engine. AI was used only to improve clarity and
            readability.
          </p>
          {explanation?.generated_at && (
            <p className="text-[9px] text-muted-foreground/50 text-center mt-1 font-mono">
              Generated at {new Date(explanation.generated_at).toLocaleTimeString()}
            </p>
          )}
        </div>
      </div>

      <style jsx>{`
        @keyframes slideInRight {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-4px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
