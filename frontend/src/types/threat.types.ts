export type Severity = "critical" | "high" | "medium" | "low" | "info";

export interface Threat {
  id: string;
  threatName: string;
  threatFamily: string;
  threatScore: number;
  severity: Severity;
  detectionTime: string;
  sha256: string;
  md5: string;
  fileSize: string;
  detectionEngine: string;
  yaraRule: string;
  description: string;
  recommendedAction: string;
  timeline: { time: string; event: string }[];
  status: "quarantined" | "removed" | "monitoring" | "resolved";
}
