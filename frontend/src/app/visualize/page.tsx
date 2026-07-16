/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useEffect, useState } from "react";
import { useDatasetStore } from "@/store/use-dataset-store";
import { BarChart3, Database, ArrowRight, Info, Sparkles } from "lucide-react";
import Link from "next/link";
import { AIExplainModal } from "@/components/ui/ai-explain-modal";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ScatterChart,
  Scatter
} from "recharts";

// A small hook to prevent Next.js SSR hydration mismatch with Recharts
function useMounted() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);
  return mounted;
}

export default function VisualizePage() {
  const { datasetId, datasetResults } = useDatasetStore();
  const mounted = useMounted();

  const [modalOpen, setModalOpen] = useState(false);
  const [modalType, setModalType] = useState<any>("chart");
  const [modalTitle, setModalTitle] = useState("");
  const [modalPayload, setModalPayload] = useState<any>(null);


  if (!datasetId || !datasetResults) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[70vh] text-center p-8">
        <div className="h-16 w-16 bg-muted/30 rounded-2xl flex items-center justify-center mb-6 border border-border">
          <BarChart3 className="h-8 w-8 text-muted-foreground" />
        </div>
        <h2 className="text-2xl font-medium text-foreground mb-2">No Data to Visualize</h2>
        <p className="text-muted-foreground max-w-sm mb-6">
          To view automatically recommended charts, you must first upload a dataset.
        </p>
        <Link href="/" className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors text-sm font-medium">
          Upload Dataset <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    );
  }

  const charts = (datasetResults.visualizations as any[]) || [];

  const renderChart = (chart: any, index: number) => {
    const { type, title, data, x_axis, y_axis, description } = chart;

    if (!data || data.length === 0) return null;

    let chartComponent = null;

    if (type === "histogram") {
      chartComponent = (
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#3C4043" />
            <XAxis dataKey="bin" stroke="#9AA0A6" fontSize={11} tickLine={false} />
            <YAxis stroke="#9AA0A6" fontSize={11} tickLine={false} />
            <Tooltip 
              contentStyle={{ backgroundColor: "#2D2F31", borderColor: "#3C4043", borderRadius: 8 }}
              labelStyle={{ color: "#E8EAED", fontWeight: "bold" }}
            />
            <Bar dataKey="count" fill="#8AB4F8" radius={[4, 4, 0, 0]} name="Frequency Count" />
          </BarChart>
        </ResponsiveContainer>
      );
    } else if (type === "bar") {
      chartComponent = (
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#3C4043" />
            <XAxis dataKey="category" stroke="#9AA0A6" fontSize={11} tickLine={false} />
            <YAxis stroke="#9AA0A6" fontSize={11} tickLine={false} />
            <Tooltip 
              contentStyle={{ backgroundColor: "#2D2F31", borderColor: "#3C4043", borderRadius: 8 }}
              labelStyle={{ color: "#E8EAED", fontWeight: "bold" }}
            />
            <Bar dataKey="count" fill="#81C995" radius={[4, 4, 0, 0]} name="Record Count" />
          </BarChart>
        </ResponsiveContainer>
      );
    } else if (type === "line") {
      chartComponent = (
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={data} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#3C4043" />
            <XAxis dataKey="date" stroke="#9AA0A6" fontSize={11} tickLine={false} />
            <YAxis stroke="#9AA0A6" fontSize={11} tickLine={false} />
            <Tooltip 
              contentStyle={{ backgroundColor: "#2D2F31", borderColor: "#3C4043", borderRadius: 8 }}
              labelStyle={{ color: "#E8EAED", fontWeight: "bold" }}
            />
            <Line type="monotone" dataKey="value" stroke="#8AB4F8" strokeWidth={2} dot={{ r: 2 }} name={y_axis} />
          </LineChart>
        </ResponsiveContainer>
      );
    } else if (type === "scatter") {
      chartComponent = (
        <ResponsiveContainer width="100%" height={320}>
          <ScatterChart margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#3C4043" />
            <XAxis type="number" dataKey="x" name={x_axis} stroke="#9AA0A6" fontSize={11} tickLine={false} />
            <YAxis type="number" dataKey="y" name={y_axis} stroke="#9AA0A6" fontSize={11} tickLine={false} />
            <Tooltip 
              contentStyle={{ backgroundColor: "#2D2F31", borderColor: "#3C4043", borderRadius: 8 }}
              cursor={{ strokeDasharray: '3 3' }} 
            />
            <Scatter name={`${x_axis} vs ${y_axis}`} data={data} fill="#8AB4F8" />
          </ScatterChart>
        </ResponsiveContainer>
      );
    } else if (type === "heatmap") {
      // Build visual correlation matrix
      const edaCorrs = datasetResults.eda?.correlations || {};
      const matrix = edaCorrs.matrix || {};
      const columns = Object.keys(matrix);

      if (columns.length === 0) return null;

      // Color-coding formula: positive correlation gets shades of blue/teal, negative gets shades of orange/rose
      const getHeatColor = (val: number) => {
        if (val === null || val === undefined) return "transparent";
        const absVal = Math.abs(val);
        if (val > 0) {
          return `rgba(138, 180, 248, ${absVal * 0.9})`; // Primary blue
        } else {
          return `rgba(242, 139, 130, ${absVal * 0.9})`; // Destructive rose
        }
      };

      chartComponent = (
        <div className="overflow-x-auto pt-4">
          <table className="w-full text-center text-xs border-collapse">
            <thead>
              <tr>
                <th className="p-2 border border-border bg-muted/40 text-left font-mono">Variable</th>
                {columns.map((col) => (
                  <th key={col} className="p-2 border border-border bg-muted/20 font-mono rotate-0 truncate max-w-[100px]">
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {columns.map((rowCol) => (
                <tr key={rowCol}>
                  <td className="p-2 border border-border bg-muted/20 text-left font-semibold font-mono truncate max-w-[120px]">
                    {rowCol}
                  </td>
                  {columns.map((colCol) => {
                    const val = matrix[rowCol]?.[colCol];
                    return (
                      <td 
                        key={colCol} 
                        className="p-3 border border-border font-mono font-medium text-foreground"
                        style={{ backgroundColor: getHeatColor(val) }}
                        title={`${rowCol} & ${colCol}: ${val}`}
                      >
                        {val !== undefined ? val.toFixed(2) : "-"}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }

    return (
      <div key={index} className="border border-border bg-card rounded-xl p-6 shadow-sm flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between mb-1">
            <h3 className="text-lg font-medium text-foreground">{title}</h3>
            <button
              onClick={() => {
                setModalType("chart");
                setModalTitle(`Explain Chart: ${title}`);
                setModalPayload(chart);
                setModalOpen(true);
              }}
              className="px-2.5 py-1.5 text-xs font-medium rounded-lg border border-border bg-card text-foreground hover:bg-muted transition-colors inline-flex items-center gap-1 shadow-sm font-sans"
            >
              <Sparkles className="h-3.5 w-3.5 text-primary" /> Explain Chart
            </button>
          </div>
          <p className="text-xs text-muted-foreground mb-6 flex items-center gap-1.5 leading-relaxed">
            <Info className="h-3.5 w-3.5 shrink-0" /> {description}
          </p>
        </div>
        <div className="flex-1 flex items-center justify-center min-h-[320px]">
          {mounted ? chartComponent : <div className="h-10 w-10 border-2 border-primary border-t-transparent rounded-full animate-spin" />}
        </div>
      </div>
    );
  };

  return (
    <div className="mx-auto max-w-6xl space-y-8 animate-in fade-in duration-500">
      <div className="border-b border-border pb-5">
        <h1 className="text-3xl font-semibold tracking-tight text-foreground">
          Recommended Visualizations
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          SAAR AI has analyzed your columns and automatically generated the most appropriate charts based on datatypes, unique spreads, and correlations.
        </p>
      </div>

      {charts.length === 0 ? (
        <div className="border border-border bg-card rounded-xl p-12 text-center text-muted-foreground shadow-sm">
          <Database className="h-12 w-12 mx-auto text-muted-foreground/30 mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-1">No Recommended Charts</h3>
          <p className="text-sm max-w-md mx-auto">
            The dataset size or column properties were insufficient to construct standard charts. Make sure you have at least one numeric or high-quality categorical column.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {charts.map((chart, index) => renderChart(chart, index))}
        </div>
      )}
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
