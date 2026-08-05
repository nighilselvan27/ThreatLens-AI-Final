export interface Report {
  id: string;
  fileName: string;
  scanDate: string;
  riskLevel: "critical" | "high" | "medium" | "low" | "safe";
  threatFamily: string | null;
  fileSize: string;
  status: "completed" | "processing" | "failed";
  analyst: string;
}
