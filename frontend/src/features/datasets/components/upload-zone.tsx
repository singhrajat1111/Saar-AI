"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { UploadCloud, FileType } from "lucide-react";
import { useDatasetStore } from "@/store/use-dataset-store";
import { cn } from "@/lib/utils";
import { apiUrl } from "@/lib/api";
import axios from "axios";

export function UploadZone() {
  const { setUploading, setUploadProgress, setDatasetId, reset } = useDatasetStore();
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;
    
    const file = acceptedFiles[0];
    const extension = file.name.split('.').pop()?.toLowerCase();
    
    if (extension !== "csv" && extension !== "xlsx" && extension !== "xls") {
      setError("Supported file formats are CSV, XLSX, and XLS.");
      return;
    }

    reset();
    setError(null);
    setUploading(true);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("client_id", "demo_client");

    try {
      const response = await axios.post(apiUrl("/api/upload"), formData, {
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1));
          setUploadProgress(percentCompleted);
        },
      });
      
      // The backend has accepted the file and started processing
      setUploadProgress(100);
      if (response.data && response.data.dataset_id) {
        setDatasetId(response.data.dataset_id);
      }
      
    } catch (err) {
      console.error(err);
      setError("Failed to upload file. Ensure backend is running.");
      setUploading(false);
    }
  }, [reset, setUploadProgress, setUploading, setDatasetId]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls']
    },
    maxFiles: 1
  });

  return (
    <div className="w-full max-w-2xl mx-auto mt-8">
      <div 
        {...getRootProps()} 
        className={cn(
          "relative flex flex-col items-center justify-center p-12 border-2 border-dashed rounded-xl transition-all cursor-pointer",
          isDragActive ? "border-primary bg-primary/5" : "border-border hover:border-primary/50 hover:bg-muted/50",
          error && "border-destructive/50 bg-destructive/5"
        )}
      >
        <input {...getInputProps()} />
        
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 mb-6">
          <UploadCloud className={cn("h-8 w-8", isDragActive ? "text-primary" : "text-muted-foreground")} />
        </div>
        
        <h3 className="text-xl font-medium text-foreground mb-2">
          {isDragActive ? "Drop your dataset here" : "Upload your dataset"}
        </h3>
        <p className="text-sm text-muted-foreground text-center max-w-sm mb-6">
          Drag and drop a CSV or Excel file, or click to browse. SAAR AI will automatically parse, clean, and analyze your data.
        </p>
        
        <div className="flex items-center gap-4 text-xs font-medium text-muted-foreground">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-background border border-border">
            <FileType className="h-3.5 w-3.5" /> CSV
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-background border border-border">
            <FileType className="h-3.5 w-3.5" /> Excel (.xlsx)
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-background border border-border">
            <FileType className="h-3.5 w-3.5" /> Excel (.xls)
          </div>
        </div>
      </div>
      
      {error && (
        <p className="mt-4 text-sm font-medium text-destructive text-center">
          {error}
        </p>
      )}
    </div>
  );
}
