import { create } from "zustand";

export interface TimelineStep {
  name: string;
  status: "pending" | "processing" | "completed" | "failed" | "skipped";
  message?: string;
  errorObject?: Record<string, any>;
}

export interface ValidationError {
  validation_code?: string;
  validation_message?: string;
  validation_error?: Record<string, any> | string;
  code?: string;
  message?: string;
  recovery?: string;
  severity?: string;
  recoverable?: boolean;
  version?: string;
  failed_step?: string;
  // Raw error object for advanced consumers
  raw?: Record<string, any>;
}

interface DatasetState {
  isUploading: boolean;
  uploadProgress: number;
  timeline: TimelineStep[];
  datasetId: string | null;
  datasetResults: Record<string, any> | null; // This will hold the final JSON from backend
  // Holds the synchronous result returned by the backend so the LiveTimeline
  // can finish its local animation and then hand it off to the dashboard.
  pendingResult: Record<string, any> | null;
  // Holds the structured validation error when the pipeline fails. The
  // LiveTimeline reads this to render the error card and stop the spinner.
  validationError: ValidationError | null;

  setUploading: (isUploading: boolean) => void;
  setUploadProgress: (progress: number) => void;
  setDatasetId: (datasetId: string | null) => void;
  updateTimeline: (stepName: string, status: TimelineStep["status"], message?: string, errorObject?: Record<string, any>) => void;
  setDatasetResults: (results: Record<string, any>) => void;
  setPendingResult: (result: Record<string, any> | null) => void;
  setValidationError: (error: ValidationError | null) => void;
  reset: () => void;
}

const INITIAL_TIMELINE: TimelineStep[] = [
  { name: "Validation", status: "pending" },
  { name: "Schema Detection", status: "pending" },
  { name: "EDA & Statistics", status: "pending" },
  { name: "Cleaning", status: "pending" },
  { name: "ML Recommendation", status: "pending" },
  { name: "Visualizations", status: "pending" },
  { name: "AI Insight Generation", status: "pending" },
  { name: "Feature Store Sync", status: "pending" },
];

export const useDatasetStore = create<DatasetState>((set) => ({
  isUploading: false,
  uploadProgress: 0,
  timeline: [...INITIAL_TIMELINE],
  datasetId: null,
  datasetResults: null,
  pendingResult: null,
  validationError: null,

  setUploading: (isUploading) => set({ isUploading }),
  setUploadProgress: (uploadProgress) => set({ uploadProgress }),
  setDatasetId: (datasetId) => set({ datasetId }),

  updateTimeline: (stepName, status, message, errorObject) => set((state) => ({
    timeline: state.timeline.map((step) =>
      step.name === stepName ? { ...step, status, message, errorObject } : step
    )
  })),

  setDatasetResults: (datasetResults) => set({ datasetResults }),

  setPendingResult: (pendingResult) => set({ pendingResult }),

  setValidationError: (validationError) => set({ validationError }),

  reset: () => set({
    isUploading: false,
    uploadProgress: 0,
    timeline: [...INITIAL_TIMELINE],
    datasetId: null,
    datasetResults: null,
    pendingResult: null,
    validationError: null
  })
}));
