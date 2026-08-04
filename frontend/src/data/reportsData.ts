import { Report } from "@/types/report.types";

const families = ["Emotet", "LockBit", "AgentTesla", "InstallCore", null, "Qakbot", "Dridex", null];
const analysts = ["S. Rahman", "J. Okafor", "M. Chen", "A. Petrov", "System (Auto)"];

function pad(n: number) {
  return n.toString().padStart(3, "0");
}

export const reports: Report[] = Array.from({ length: 47 }).map((_, i) => {
  const riskLevels: Report["riskLevel"][] = ["critical", "high", "medium", "low", "safe"];
  const risk = riskLevels[i % riskLevels.length];
  return {
    id: `RPT-${pad(i + 1)}`,
    fileName: `scan_batch_${pad(i + 1)}_${["invoice", "installer", "driver", "photo", "report"][i % 5]}.${["exe", "dll", "docm", "zip", "scr"][i % 5]}`,
    scanDate: new Date(Date.now() - i * 3.2 * 60 * 60 * 1000).toISOString(),
    riskLevel: risk,
    threatFamily: risk === "safe" ? null : families[i % families.length],
    fileSize: `${(Math.random() * 5 + 0.1).toFixed(1)} MB`,
    status: i % 11 === 0 ? "processing" : i % 17 === 0 ? "failed" : "completed",
    analyst: analysts[i % analysts.length],
  };
});
