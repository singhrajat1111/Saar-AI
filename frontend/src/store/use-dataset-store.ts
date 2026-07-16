import { create } from "zustand";

export interface TimelineStep {
  name: string;
  status: "pending" | "processing" | "completed" | "failed";
  message?: string;
  errorObject?: Record<string, any>;
}

interface DatasetState {
  isUploading: boolean;
  uploadProgress: number;
  timeline: TimelineStep[];
  datasetId: string | null;
  datasetResults: Record<string, any> | null; // This will hold the final JSON from backend
  
  setUploading: (isUploading: boolean) => void;
  setUploadProgress: (progress: number) => void;
  setDatasetId: (datasetId: string | null) => void;
  updateTimeline: (stepName: string, status: TimelineStep["status"], message?: string, errorObject?: Record<string, any>) => void;
  setDatasetResults: (results: Record<string, any>) => void;
  reset: () => void;
}

const INITIAL_TIMELINE: TimelineStep[] = [
  { name: "Validation", status: "pending" },
  { name: "Schema Detection", status: "pending" },
  { name: "EDA & Statistics", status: "pending" },
  { name: "ML Recommendation", status: "pending" },
  { name: "AI Insight Generation", status: "pending" },
  { name: "Feature Store Sync", status: "pending" },
];

export const useDatasetStore = create<DatasetState>((set) => ({
  isUploading: false,
  uploadProgress: 0,
  timeline: [...INITIAL_TIMELINE],
  datasetId: null,
  datasetResults: null,
  
  setUploading: (isUploading) => set({ isUploading }),
  setUploadProgress: (uploadProgress) => set({ uploadProgress }),
  setDatasetId: (datasetId) => set({ datasetId }),
  
  updateTimeline: (stepName, status, message, errorObject) => set((state) => ({
    timeline: state.timeline.map((step) => 
      step.name === stepName ? { ...step, status, message, errorObject } : step
    )
  })),
  
  setDatasetResults: (datasetResults) => set({ datasetResults }),
  
  reset: () => set({
    isUploading: false,
    uploadProgress: 0,
    timeline: [...INITIAL_TIMELINE],
    datasetId: null,
    datasetResults: null
  })
}));
