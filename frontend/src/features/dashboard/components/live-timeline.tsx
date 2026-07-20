"use client";

import { useEffect, useRef } from "react";
import { useDatasetStore } from "@/store/use-dataset-store";
import {
  CheckCircle2,
  Circle,
  Loader2,
  XCircle,
  Ban,
  RotateCcw,
  UploadCloud,
  FileWarning,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { wsUrl } from "@/lib/api";

export function LiveTimeline() {
  const {
    timeline,
    pendingResult,
    validationError,
    updateTimeline,
    setDatasetResults,
    setUploading,
    setValidationError,
    reset,
  } = useDatasetStore();
  const replayStartedRef = useRef(false);
  const replayCancelledRef = useRef(false);

  useEffect(() => {
    const ws = new WebSocket(wsUrl("/api/ws/demo_client"));

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "timeline_update") {
          updateTimeline(data.step, data.status, data.message, data.results?.error_object);
          if (data.status === "failed") {
            const errorObject = data.results?.error_object || data.error_object || {};
            setValidationError({
              validation_code: errorObject.code || data.results?.error_code,
              validation_message: errorObject.message || data.message,
              validation_error: errorObject,
              code: errorObject.code || data.results?.error_code,
              message: errorObject.message || data.message,
              recovery: errorObject.recovery,
              severity: errorObject.severity,
              recoverable: errorObject.recoverable,
              version: errorObject.version,
              failed_step: data.step || "validation",
              raw: errorObject,
            });
          }
        } else if (data.type === "workflow_complete") {
          setDatasetResults(data.results);
        }
      } catch (err) {
        console.error("Failed to parse websocket message", err);
      }
    };

    return () => {
      ws.close();
    };
  }, [updateTimeline, setDatasetResults]);

  // ── FAILURE DETECTION (reactive) ──────────────────────────────────────
  // Runs whenever validationError changes. The upload-zone response handler
  // or the WebSocket onmessage handler sets validationError *after* mount.
  // This effect must cancel any in-progress success replay and mark the
  // timeline accordingly.
  useEffect(() => {
    if (!validationError) return;

    replayCancelledRef.current = true;

    const failedStepName =
      STEP_FOR_FAILED[validationError.failed_step || "validation"] || "Validation";

    updateTimeline(failedStepName, "failed", validationError.message, validationError.raw);

    // Read the latest timeline snapshot from the store so we can mark every
    // step after the failure as "skipped".
    const snap = useDatasetStore.getState().timeline;
    const failedIdx = snap.findIndex((s) => s.name === failedStepName);
    for (let i = failedIdx + 1; i < snap.length; i++) {
      if (snap[i].status !== "skipped") {
        updateTimeline(snap[i].name, "skipped");
      }
    }
  }, [validationError, updateTimeline]);

  // ── SUCCESS ANIMATION (one-shot) ──────────────────────────────────────
  // Runs once on mount. If validationError was already set at mount time
  // (unlikely but possible), we bail immediately. Otherwise we animate each
  // pipeline step with staggered delays. The async loop checks
  // replayCancelledRef.current on every iteration so the failure useEffect
  // above can abort it at any point.
  useEffect(() => {
    if (replayStartedRef.current) return;
    if (timeline.length === 0) return;
    if (validationError) return;

    replayStartedRef.current = true;

    const allCompleted = timeline.every((s) => s.status === "completed");
    if (allCompleted) return;

    const stepDelays = [350, 450, 500, 300, 500, 500, 500, 400];
    let cancelled = false;

    (async () => {
      for (let i = 0; i < timeline.length; i++) {
        if (cancelled || replayCancelledRef.current) return;
        const step = timeline[i];
        const delay = stepDelays[i] ?? 400;

        updateTimeline(step.name, "processing");
        await new Promise((r) => setTimeout(r, delay));
        if (cancelled || replayCancelledRef.current) return;
        updateTimeline(step.name, "completed", "Done");
      }

      if (cancelled || replayCancelledRef.current) return;

      // The animation may finish before the synchronous backend POST
      // returns. Poll the store for the pendingResult (set by upload-zone
      // when the POST resolves) or for datasetResults (set by the
      // WebSocket "workflow_complete" handler). Use getState() to avoid
      // the stale-closure problem — the pendingResult captured at mount
      // time is always null.
      let result = useDatasetStore.getState().pendingResult;
      let waited = 0;
      while (!result && !useDatasetStore.getState().datasetResults && waited < 15000) {
        await new Promise((r) => setTimeout(r, 200));
        result = useDatasetStore.getState().pendingResult;
        waited += 200;
      }

      if (cancelled || replayCancelledRef.current) return;

      if (result) {
        setDatasetResults(result);
      }
      setUploading(false);
    })();

    return () => {
      cancelled = true;
    };
    // We intentionally only run this once on mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const failedStep = timeline.find((step) => step.status === "failed");
  const errorObj = failedStep?.errorObject ?? (validationError?.raw as Record<string, any> | undefined);

  // Failure card is visible whenever we have either a marked failed step
  // OR a validation error sitting in the store (covers the edge case where
  // the timeline step names don't line up with the failure step).
  const showFailureCard = Boolean(failedStep || validationError);
  const displayError: {
    code?: string;
    message?: string;
    recovery?: string;
  } | null = validationError
    ? {
        code: validationError.code,
        message: validationError.message,
        recovery: validationError.recovery,
      }
    : failedStep
    ? {
        code: errorObj?.code,
        message: failedStep.message || errorObj?.message,
        recovery: errorObj?.recovery,
      }
    : null;

  // Stable handlers for the two recovery buttons.
  const handleBackToUpload = () => {
    // Clear local error state and unmount the timeline.
    setValidationError(null);
    setUploading(false);
    reset();
  };

  const handleUploadAnother = () => {
    // Same as back-to-upload; the user can re-drop a new file in the
    // resulting UploadZone. We keep the naming per the spec.
    setValidationError(null);
    setUploading(false);
    reset();
  };

  return (
    <div className="w-full max-w-2xl mx-auto mt-12 bg-card border border-border rounded-xl p-6 shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-medium text-foreground">Live Analysis Pipeline</h3>
        {validationError && (
          <span className="px-2 py-0.5 text-[10px] font-bold rounded uppercase tracking-wider bg-destructive/10 text-destructive border border-destructive/20">
            Failed
          </span>
        )}
      </div>

      <div className="space-y-6">
        {timeline.map((step, index) => {
          const isPending = step.status === "pending";
          const isProcessing = step.status === "processing";
          const isCompleted = step.status === "completed";
          const isFailed = step.status === "failed";
          const isSkipped = step.status === "skipped";

          // Draw connecting line if not the last item
          const isLast = index === timeline.length - 1;

          return (
            <div key={step.name} className="relative flex gap-4">
              {!isLast && (
                <div
                  className={cn(
                    "absolute left-3 top-8 bottom-[-24px] w-0.5",
                    isCompleted ? "bg-primary" : "bg-border"
                  )}
                />
              )}

              <div className="relative z-10 flex h-6 w-6 shrink-0 items-center justify-center bg-card">
                {isPending && <Circle className="h-5 w-5 text-muted-foreground opacity-30" />}
                {isProcessing && <Loader2 className="h-5 w-5 text-primary animate-spin" />}
                {isCompleted && <CheckCircle2 className="h-5 w-5 text-primary" />}
                {isFailed && <XCircle className="h-5 w-5 text-destructive" />}
                {isSkipped && <Ban className="h-5 w-5 text-muted-foreground/40" />}
              </div>

              <div className="flex flex-col pb-1">
                <span className={cn(
                  "text-sm font-medium",
                  isPending && "text-muted-foreground",
                  isProcessing && "text-foreground",
                  isCompleted && "text-foreground",
                  isFailed && "text-destructive",
                  isSkipped && "text-muted-foreground/50 line-through"
                )}>
                  {step.name}
                </span>
                {step.message && (
                  <span className="text-xs text-muted-foreground mt-0.5">
                    {step.message}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {showFailureCard && displayError && (
        <div
          data-testid="validation-error-card"
          className="mt-8 border border-destructive/30 bg-destructive/5 rounded-xl p-6 animate-in fade-in slide-in-from-bottom duration-300"
        >
          <div className="flex items-start gap-3 mb-4">
            <div className="h-10 w-10 rounded-xl bg-destructive/15 flex items-center justify-center shrink-0">
              <FileWarning className="h-5 w-5 text-destructive" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 text-destructive font-semibold text-sm">
                <XCircle className="h-4 w-4" />
                <span>
                  {displayError.code
                    ? humanizeCode(displayError.code)
                    : (failedStep?.name || "Validation") + " Failed"}
                </span>
              </div>
              {displayError.code && (
                <div className="mt-1.5 inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-destructive/10 border border-destructive/20 text-[10px] font-mono font-bold text-destructive uppercase tracking-wider">
                  {displayError.code}
                </div>
              )}
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground block mb-1">
                Message
              </span>
              <p className="text-sm text-foreground/90 leading-relaxed">
                {displayError.message || "An error occurred during dataset processing."}
              </p>
            </div>

            {displayError.recovery && (
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground block mb-1">
                  What you can do
                </span>
                <p className="text-sm text-foreground/90 leading-relaxed">
                  {displayError.recovery}
                </p>
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-2">
              <button
                onClick={handleBackToUpload}
                className="w-full py-2 px-4 rounded-lg border border-border bg-card text-foreground hover:bg-muted transition-colors text-sm font-medium inline-flex items-center justify-center gap-2"
              >
                <RotateCcw className="h-4 w-4" />
                Back to Upload
              </button>
              <button
                onClick={handleUploadAnother}
                className="w-full py-2 px-4 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors text-sm font-medium inline-flex items-center justify-center gap-2 shadow-sm"
              >
                <UploadCloud className="h-4 w-4" />
                Upload Another Dataset
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Maps the backend's "failed_step" value (e.g. "validation", "schema", "eda",
// "ml", "llm") to the timeline step name we display.
const STEP_FOR_FAILED: Record<string, string> = {
  validation: "Validation",
  schema: "Schema Detection",
  eda: "EDA & Statistics",
  cleaning: "Cleaning",
  ml: "ML Recommendation",
  visualizations: "Visualizations",
  llm: "AI Insight Generation",
  ai: "AI Insight Generation",
  feature_store: "Feature Store Sync",
};

// Renders a human-friendly title from a validation code constant, e.g.
// "DUPLICATE_HEADERS" -> "Duplicate Column Headers Detected".
function humanizeCode(code: string): string {
  const map: Record<string, string> = {
    DUPLICATE_HEADERS: "Duplicate Column Headers Detected",
    BLANK_HEADERS: "Blank Column Headers Detected",
    NO_COLUMNS: "No Columns Found",
    EMPTY_FILE: "Empty File",
    EMPTY_DATASET: "Empty Dataset",
    ALL_NULL_DATASET: "All-Null Dataset",
    UNSUPPORTED_FILE: "Unsupported File Format",
    CORRUPTED_FILE: "Corrupted File",
    INVALID_ENCODING: "Invalid File Encoding",
    INVALID_HEADER_CHARACTERS: "Invalid Header Characters",
    UNEXPECTED_PIPELINE_ERROR: "Pipeline Error",
    HIGH_MISSINGNESS: "High Missingness Detected",
    VERY_SMALL_DATASET: "Very Small Dataset",
    ONE_ROW_DATASET: "Single Row Dataset",
    ONE_COLUMN_DATASET: "Single Column Dataset",
    CONSTANT_COLUMN: "Constant Column Detected",
    HIGH_OUTLIERS: "High Outlier Count",
    MIXED_DATATYPE_COLUMN: "Mixed Data Types in Column",
    LONG_COLUMN_NAME: "Column Name Too Long",
    DUPLICATE_ROWS: "Duplicate Rows Detected",
    INFINITY_VALUES: "Infinity Values Detected",
    EMPTY_STRING_VALUES: "Empty String Values Detected",
    LOW_STATISTICAL_RELIABILITY: "Low Statistical Reliability",
  };
  return map[code] || "Dataset Validation Failed";
}
