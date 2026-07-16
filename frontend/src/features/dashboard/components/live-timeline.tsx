"use client";

import { useEffect } from "react";
import { useDatasetStore } from "@/store/use-dataset-store";
import { CheckCircle2, Circle, Loader2, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { wsUrl } from "@/lib/api";

export function LiveTimeline() {
  const { timeline, updateTimeline, setDatasetResults, reset } = useDatasetStore();

  useEffect(() => {
    const ws = new WebSocket(wsUrl("/api/ws/demo_client"));

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "timeline_update") {
          updateTimeline(data.step, data.status, data.message, data.results?.error_object);
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

  const failedStep = timeline.find((step) => step.status === "failed");
  const errorObj = failedStep?.errorObject;

  return (
    <div className="w-full max-w-2xl mx-auto mt-12 bg-card border border-border rounded-xl p-6 shadow-sm">
      <h3 className="text-lg font-medium text-foreground mb-6">Live Analysis Pipeline</h3>
      
      <div className="space-y-6">
        {timeline.map((step, index) => {
          const isPending = step.status === "pending";
          const isProcessing = step.status === "processing";
          const isCompleted = step.status === "completed";
          const isFailed = step.status === "failed";
          
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
              </div>
              
              <div className="flex flex-col pb-1">
                <span className={cn(
                  "text-sm font-medium",
                  isPending && "text-muted-foreground",
                  isProcessing && "text-foreground",
                  isCompleted && "text-foreground",
                  isFailed && "text-destructive"
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

      {failedStep && (
        <div className="mt-8 border border-destructive/20 bg-destructive/5 rounded-xl p-5 animate-in fade-in slide-in-from-bottom duration-300">
          <div className="flex items-center gap-2 text-destructive font-medium text-sm mb-2.5">
            <XCircle className="h-5 w-5" />
            <span>Dataset Validation Failed ({errorObj?.code || "PIPELINE_ERROR"})</span>
          </div>
          <p className="text-sm text-foreground/90 leading-relaxed mb-4">
            {errorObj?.message || failedStep.message || "An error occurred during dataset processing."}
          </p>
          <div className="text-xs text-muted-foreground mb-5 space-y-2">
            <span className="font-semibold text-foreground block">What you can do:</span>
            <ul className="list-disc pl-4 space-y-1">
              <li>Add at least one row of data to the dataset.</li>
              <li>Ensure all columns have valid, non-duplicate header names.</li>
              <li>Upload another dataset file.</li>
            </ul>
          </div>
          <button
            onClick={reset}
            className="w-full py-2 px-4 rounded-lg bg-destructive text-destructive-foreground hover:bg-destructive/90 transition-colors text-sm font-medium shadow-sm"
          >
            Back to Upload
          </button>
        </div>
      )}
    </div>
  );
}
