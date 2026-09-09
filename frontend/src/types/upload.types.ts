export interface UploadedFile {
  id: string;
  name: string;
  size: string;
  type: string;
  progress: number;
  status: "queued" | "uploading" | "analyzing" | "completed" | "failed";
  riskLevel?: "critical" | "high" | "medium" | "low" | "safe";
  sha256?: string;
  md5?: string;
  uploadedAt: string;
}
