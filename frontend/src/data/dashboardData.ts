import { DashboardStats } from "@/types/dashboard.types";

export const dashboardStats: DashboardStats = {
  totalFilesScanned: 48213,
  malwareDetected: 1847,
  safeFiles: 46021,
  threatScore: 34,
  todaysScans: 312,
  activeAlerts: 9,
};

export const recentActivity = [
  { id: "a1", actor: "System", action: "Quarantined file trojan_dropper.exe", time: "2 min ago" },
  { id: "a2", actor: "S. Rahman", action: "Marked alert #4471 as resolved", time: "14 min ago" },
  { id: "a3", actor: "System", action: "New YARA rule deployed: Emotet_v3", time: "41 min ago" },
  { id: "a4", actor: "J. Okafor", action: "Exported weekly threat report (CSV)", time: "1 hr ago" },
  { id: "a5", actor: "System", action: "Static analysis completed for 214 files", time: "2 hr ago" },
];

export const recentScans = [
  { id: "s1", fileName: "invoice_2026_q3.pdf.exe", riskLevel: "critical", time: "3 min ago" },
  { id: "s2", fileName: "update_installer.msi", riskLevel: "safe", time: "18 min ago" },
  { id: "s3", fileName: "photo_gallery.scr", riskLevel: "high", time: "27 min ago" },
  { id: "s4", fileName: "quarterly_report.docm", riskLevel: "medium", time: "52 min ago" },
  { id: "s5", fileName: "driver_pack.zip", riskLevel: "safe", time: "1 hr ago" },
] as const;
