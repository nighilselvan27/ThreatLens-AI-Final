import { useCallback, useEffect, useState } from "react";
import { UploadCloud, FileArchive, ScanLine, Hash, Clock, FileWarning } from "lucide-react";
import { useAppDispatch, useAppSelector } from "@/redux/hooks";
import { fetchUploadHistory, addActiveUpload, updateActiveUploadProgress, completeUpload } from "@/redux/slices/uploadSlice";
import { uploadApi } from "@/api/uploadApi";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import ProgressBar from "@/components/ui/ProgressBar";
import { Table, THead, TBody, Tr, Th, Td } from "@/components/ui/Table";
import { useToast } from "@/hooks/useToast";
import { truncateHash, timeAgo } from "@/utils/formatters";
import { UploadedFile } from "@/types/upload.types";

// ── IMPROVEMENT 1: File upload validation ──────────────────────────────
// Reasonable allow-list for a malware-scanning demo: common executable,
// document, script, and archive types an analyst would actually submit.
const ALLOWED_EXTENSIONS = [
  ".exe", ".dll", ".msi", ".scr", ".bat", ".ps1", ".js",
  ".pdf", ".doc", ".docx", ".docm", ".xls", ".xlsx",
  ".zip", ".rar",
];
const MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024; // 50 MB

function getExtension(fileName: string): string {
  const idx = fileName.lastIndexOf(".");
  return idx === -1 ? "" : fileName.slice(idx).toLowerCase();
}

function validateFile(file: File): { valid: true } | { valid: false; reason: string } {
  const ext = getExtension(file.name);

  if (!ALLOWED_EXTENSIONS.includes(ext)) {
    return {
      valid: false,
      reason: `"${file.name}" has an unsupported file type (${ext || "unknown"}). Supported types: ${ALLOWED_EXTENSIONS.join(", ")}.`,
    };
  }

  if (file.size > MAX_FILE_SIZE_BYTES) {
    return {
      valid: false,
      reason: `"${file.name}" is ${(file.size / (1024 * 1024)).toFixed(1)} MB, which exceeds the 50 MB limit.`,
    };
  }

  return { valid: true };
}
// ─────────────────────────────────────────────────────────────────────

export default function UploadPage() {
  const dispatch = useAppDispatch();
  const { history, activeUploads } = useAppSelector((s) => s.upload);
  const [isDragging, setIsDragging] = useState(false);
  const [selectedResult, setSelectedResult] = useState<UploadedFile | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    dispatch(fetchUploadHistory());
  }, [dispatch]);

  const handleFiles = useCallback(
    async (files: FileList | null) => {
      if (!files || files.length === 0) return;

      for (const file of Array.from(files)) {
        // Validate before doing anything else — invalid files never start
        // the simulated scan and never touch Redux state.
        const validation = validateFile(file);
        if (!validation.valid) {
          toast({ title: "File rejected", description: validation.reason, variant: "error" });
          continue;
        }

        const id = `up-${Date.now()}-${Math.random().toString(36).slice(2)}`;
        const draft: UploadedFile = {
          id,
          name: file.name,
          size: `${(file.size / (1024 * 1024)).toFixed(2)} MB`,
          type: file.type || "unknown",
          progress: 0,
          status: "uploading",
          uploadedAt: new Date().toISOString(),
        };
        dispatch(addActiveUpload(draft));

        const result = await uploadApi.uploadFile(file, (pct) => {
          dispatch(updateActiveUploadProgress({ id, progress: pct, status: pct === 100 ? "analyzing" : "uploading" }));
        });

        const finalResult = { ...result, id };
        dispatch(completeUpload(finalResult));
        setSelectedResult(finalResult);
        toast({
          title: "Scan complete",
          description: `${file.name} classified as ${finalResult.riskLevel}.`,
          variant: finalResult.riskLevel === "safe" ? "success" : "warning",
        });
      }
    },
    [dispatch, toast]
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-xl font-semibold text-slate-100">Upload & Scan</h1>
        <p className="text-sm text-muted mt-1">Submit files for static analysis and ML-based classification.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setIsDragging(false);
              handleFiles(e.dataTransfer.files);
            }}
            className={`glass-panel border-2 border-dashed p-10 text-center transition-colors relative overflow-hidden ${
              isDragging ? "border-accent-cyan bg-accent-cyan/5" : "border-border"
            }`}
          >
            {isDragging && <div className="absolute inset-x-0 top-0 h-1 bg-accent-cyan animate-scan" />}
            <div className="h-14 w-14 rounded-2xl bg-accent-cyan/10 flex items-center justify-center mx-auto mb-4">
              <UploadCloud className="h-7 w-7 text-accent-cyan" />
            </div>
            <p className="font-medium text-slate-100 mb-1">Drag & drop files to scan</p>
            <p className="text-sm text-muted mb-2">or browse from your device — executables, documents, and archives supported</p>
            <p className="text-xs text-slate-500 mb-5">
              Supported: {ALLOWED_EXTENSIONS.join(", ")} · Max size: 50 MB
            </p>
            <label className="inline-flex items-center justify-center gap-2 rounded-lg font-medium h-10 px-4 text-sm bg-gradient-to-r from-accent-blue to-accent-cyan text-slate-950 hover:shadow-glow hover:brightness-110 cursor-pointer transition-all">
              <input
                type="file"
                multiple
                accept={ALLOWED_EXTENSIONS.join(",")}
                className="hidden"
                onChange={(e) => handleFiles(e.target.files)}
              />
              Browse Files
            </label>
          </div>

          {activeUploads.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Active Scans</CardTitle>
                <ScanLine className="h-4 w-4 text-accent-cyan animate-pulse" />
              </CardHeader>
              <div className="space-y-4">
                {activeUploads.map((f) => (
                  <div key={f.id}>
                    <div className="flex justify-between text-sm mb-1.5">
                      <span className="text-slate-200 truncate">{f.name}</span>
                      <span className="text-xs text-muted capitalize">{f.status}</span>
                    </div>
                    <ProgressBar value={f.progress} />
                  </div>
                ))}
              </div>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Upload History</CardTitle>
              <FileArchive className="h-4 w-4 text-muted" />
            </CardHeader>
            <Table>
              <THead>
                <Th>File</Th>
                <Th>Size</Th>
                <Th>Risk</Th>
                <Th>Uploaded</Th>
              </THead>
              <TBody>
                {history.map((f) => (
                  <Tr key={f.id} className="cursor-pointer" onClick={() => setSelectedResult(f)}>
                    <Td className="font-mono text-xs">{f.name}</Td>
                    <Td>{f.size}</Td>
                    <Td>
                      <Badge severity={(f.riskLevel as any) ?? "safe"} />
                    </Td>
                    <Td className="text-xs text-muted">{timeAgo(f.uploadedAt)}</Td>
                  </Tr>
                ))}
              </TBody>
            </Table>
          </Card>
        </div>

        <div>
          <Card className="sticky top-20">
            <CardHeader>
              <CardTitle>Scan Result</CardTitle>
            </CardHeader>

            {selectedResult ? (
              // ── IMPROVEMENT 2: result organized into clear sections ──
              <div className="space-y-5">
                {/* B. Scan Result */}
                <div>
                  <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2.5">
                    Scan Result
                  </p>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center justify-between">
                      <span className="text-muted">Status</span>
                      <span className="text-slate-200 capitalize">{selectedResult.status}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted">Risk Level</span>
                      <Badge severity={(selectedResult.riskLevel as any) ?? "safe"} />
                    </div>
                  </div>
                </div>

                {/* A. File Information */}
                <div className="border-t border-white/5 pt-4">
                  <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2.5">
                    File Information
                  </p>
                  <div className="space-y-1.5 text-sm">
                    <div className="flex justify-between gap-3">
                      <span className="text-muted shrink-0">Name</span>
                      <span className="text-slate-200 truncate text-right">{selectedResult.name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted">Size</span>
                      <span className="text-slate-200">{selectedResult.size}</span>
                    </div>
                    <div className="flex justify-between gap-3">
                      <span className="text-muted shrink-0">Type</span>
                      <span className="text-slate-200 truncate text-right">{selectedResult.type}</span>
                    </div>
                  </div>
                </div>

                {/* C. Analysis Details */}
                <div className="border-t border-white/5 pt-4">
                  <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2.5">
                    Analysis Details
                  </p>
                  <div className="rounded-lg bg-background-surface border border-border p-3 space-y-2.5 text-xs">
                    <div className="flex items-start gap-2">
                      <Hash className="h-3.5 w-3.5 text-muted mt-0.5 shrink-0" />
                      <div className="min-w-0">
                        <p className="text-muted mb-0.5">SHA-256</p>
                        <p className="font-mono text-slate-300 break-all">
                          {truncateHash(selectedResult.sha256 ?? "—", 14)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-start gap-2">
                      <Hash className="h-3.5 w-3.5 text-muted mt-0.5 shrink-0" />
                      <div className="min-w-0">
                        <p className="text-muted mb-0.5">MD5</p>
                        <p className="font-mono text-slate-300 break-all">{selectedResult.md5}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Clock className="h-3.5 w-3.5 text-muted shrink-0" />
                      <p className="text-slate-300">Scanned {timeAgo(selectedResult.uploadedAt)}</p>
                    </div>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-2 leading-relaxed">
                    Demo mode: risk level and hash values shown here are simulated mock data for
                    UI demonstration, not output from a real malware-detection engine.
                  </p>
                </div>

                <Button variant="secondary" className="w-full" size="sm">
                  View Full Report
                </Button>
              </div>
            ) : (
              <div className="text-center py-6">
                <FileWarning className="h-6 w-6 text-slate-700 mx-auto mb-3" />
                <p className="text-sm text-muted">
                  Upload a file to see static analysis results and risk classification here.
                </p>
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}