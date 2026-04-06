"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { scans, type Scan, type ScanWithMetrics } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FileText, ChevronDown, ChevronUp, Upload, FileSpreadsheet } from "lucide-react";

const ACCEPT_PDF = "application/pdf";
const ACCEPT_CSV = ".csv,text/csv,application/csv";

function ScanMetricsRow({ scanId }: { scanId: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ["scan", scanId],
    queryFn: () => scans.get(scanId),
  });

  if (isLoading)
    return <p className="text-xs text-muted-foreground px-4 pb-4">Loading metrics…</p>;
  if (!data) return null;

  const metrics = data.metrics.filter((m) => m.metric_value !== null);

  return (
    <div className="px-4 pb-4 grid grid-cols-2 md:grid-cols-4 gap-2">
      {metrics.map((m) => (
        <div key={m.metric_key} className="rounded-lg bg-white/5 p-2">
          <p className="text-xs text-muted-foreground capitalize">
            {m.metric_key.replace(/_/g, " ")}
          </p>
          <p className="text-sm font-semibold text-foreground">
            {m.metric_value?.toFixed(2)}
          </p>
        </div>
      ))}
    </div>
  );
}

function ScanRow({ scan }: { scan: Scan }) {
  const [expanded, setExpanded] = useState(false);
  const isCsv = scan.storage_path?.endsWith(".csv");

  return (
    <div className="glass-card overflow-hidden">
      <button
        className="w-full flex items-center justify-between p-4 text-left hover:bg-white/5 transition-colors"
        onClick={() => setExpanded((e) => !e)}
      >
        <div className="flex items-center gap-3">
          {isCsv ? (
            <FileSpreadsheet className="h-5 w-5 text-cyan-400" />
          ) : (
            <FileText className="h-5 w-5 text-purple-400" />
          )}
          <div>
            <p className="font-medium text-foreground">{scan.scan_date}</p>
            <p className="text-xs text-muted-foreground">
              {isCsv ? "CSV" : "PDF"} · Uploaded{" "}
              {new Date(scan.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>
        {expanded ? (
          <ChevronUp className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        )}
      </button>
      {expanded && <ScanMetricsRow scanId={scan.id} />}
    </div>
  );
}

type UploadMode = "pdf" | "csv";

export default function ScansPage() {
  const queryClient = useQueryClient();
  const [mode, setMode] = useState<UploadMode>("csv");
  const [file, setFile] = useState<File | null>(null);
  const [scanDate, setScanDate] = useState("");
  const [uploadError, setUploadError] = useState<string | null>(null);

  const { data: scanList, isLoading } = useQuery({
    queryKey: ["scans"],
    queryFn: scans.list,
  });

  const handleSuccess = () => {
    queryClient.invalidateQueries({ queryKey: ["scans"] });
    queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    setFile(null);
    setScanDate("");
    setUploadError(null);
  };

  const handleError = (e: unknown) => {
    const err = e as { detail?: string };
    setUploadError(err?.detail ?? "Upload failed");
  };

  const pdfMutation = useMutation({
    mutationFn: () => scans.upload(file!, scanDate),
    onSuccess: handleSuccess,
    onError: handleError,
  });

  const csvMutation = useMutation({
    mutationFn: () => scans.uploadCsv(file!, scanDate || undefined),
    onSuccess: handleSuccess,
    onError: handleError,
  });

  const activeMutation = mode === "pdf" ? pdfMutation : csvMutation;
  const isPending = activeMutation.isPending;

  const canSubmit =
    file !== null &&
    (mode === "csv" ? true : scanDate !== "") && // CSV date is optional (may be in file)
    !isPending;

  const switchMode = (m: UploadMode) => {
    setMode(m);
    setFile(null);
    setUploadError(null);
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold gradient-text">Scan History</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Upload your InBody scan results — PDF report or CSV export
        </p>
      </div>

      {/* Upload Form */}
      <div className="glass-card p-6 space-y-5">
        <h2 className="text-sm font-semibold text-foreground">Upload New Scan</h2>

        {/* Mode toggle */}
        <div className="flex rounded-lg bg-white/5 p-1 gap-1 w-fit">
          {(["csv", "pdf"] as UploadMode[]).map((m) => (
            <button
              key={m}
              onClick={() => switchMode(m)}
              className={`px-4 py-1.5 rounded-md text-xs font-medium transition-colors ${
                mode === m
                  ? "bg-purple-600 text-white"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {m.toUpperCase()}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* File picker */}
          <div className="space-y-1.5">
            <Label>{mode === "csv" ? "CSV File" : "PDF File"}</Label>
            <div
              className="flex items-center gap-3 rounded-lg border border-dashed border-white/20 p-4 cursor-pointer hover:border-purple-500/50 transition-colors"
              onClick={() => document.getElementById("scan-file-input")?.click()}
            >
              {mode === "csv" ? (
                <FileSpreadsheet className="h-5 w-5 text-cyan-400 shrink-0" />
              ) : (
                <Upload className="h-5 w-5 text-purple-400 shrink-0" />
              )}
              <span className="text-sm text-muted-foreground truncate">
                {file ? file.name : `Click to select ${mode.toUpperCase()}`}
              </span>
              <input
                id="scan-file-input"
                type="file"
                accept={mode === "csv" ? ACCEPT_CSV : ACCEPT_PDF}
                className="hidden"
                onChange={(e) => {
                  setFile(e.target.files?.[0] ?? null);
                  setUploadError(null);
                }}
              />
            </div>
          </div>

          {/* Date field */}
          <div className="space-y-1.5">
            <Label htmlFor="scan-date">
              Scan Date{mode === "csv" && <span className="text-muted-foreground ml-1">(optional if in CSV)</span>}
            </Label>
            <Input
              id="scan-date"
              type="date"
              value={scanDate}
              onChange={(e) => setScanDate(e.target.value)}
              className="bg-white/5 border-white/10 text-foreground"
            />
          </div>
        </div>

        {mode === "csv" && (
          <p className="text-xs text-muted-foreground">
            Supports InBody CSV exports (tabular multi-column or key-value format).
            If the file contains a date column it will be detected automatically.
          </p>
        )}

        {uploadError && (
          <div className="rounded-lg bg-destructive/10 border border-destructive/30 px-4 py-3 text-sm text-destructive">
            {uploadError}
          </div>
        )}

        <Button
          onClick={() => activeMutation.mutate()}
          disabled={!canSubmit}
          className="btn-primary-glass"
        >
          {isPending ? (
            <span className="flex items-center gap-2">
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              Uploading &amp; Extracting…
            </span>
          ) : (
            `Upload ${mode.toUpperCase()}`
          )}
        </Button>
      </div>

      {/* Scan List */}
      {isLoading ? (
        <div className="flex h-32 items-center justify-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-purple-500 border-t-transparent" />
        </div>
      ) : (
        <div className="space-y-3">
          {(scanList ?? []).length === 0 ? (
            <p className="text-muted-foreground text-center py-8">No scans uploaded yet.</p>
          ) : (
            (scanList ?? []).map((s) => <ScanRow key={s.id} scan={s} />)
          )}
        </div>
      )}
    </div>
  );
}
