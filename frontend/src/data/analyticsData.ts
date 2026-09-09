export const monthlyThreatDetection = [
  { month: "Feb", malware: 210, safe: 3200 },
  { month: "Mar", malware: 285, safe: 3450 },
  { month: "Apr", malware: 198, safe: 3610 },
  { month: "May", malware: 340, safe: 3380 },
  { month: "Jun", malware: 410, safe: 3900 },
  { month: "Jul", malware: 372, safe: 4120 },
  { month: "Aug", malware: 156, safe: 1580 },
];

export const weeklyUploads = [
  { day: "Mon", uploads: 412 },
  { day: "Tue", uploads: 528 },
  { day: "Wed", uploads: 489 },
  { day: "Thu", uploads: 601 },
  { day: "Fri", uploads: 574 },
  { day: "Sat", uploads: 203 },
  { day: "Sun", uploads: 167 },
];

export const threatLevelDistribution = [
  { name: "Critical", value: 184, color: "#f43f5e" },
  { name: "High", value: 412, color: "#fb923c" },
  { name: "Medium", value: 726, color: "#facc15" },
  { name: "Low", value: 525, color: "#34d399" },
];

export const topMalwareFamilies = [
  { family: "Emotet", detections: 412 },
  { family: "LockBit", detections: 318 },
  { family: "AgentTesla", detections: 276 },
  { family: "Qakbot", detections: 201 },
  { family: "Dridex", detections: 164 },
  { family: "InstallCore", detections: 142 },
];

export const riskScoreDistribution = [
  { range: "0-20", count: 1820 },
  { range: "21-40", count: 940 },
  { range: "41-60", count: 610 },
  { range: "61-80", count: 384 },
  { range: "81-100", count: 212 },
];

export const classificationResults = [
  { name: "Trojan", value: 38 },
  { name: "Ransomware", value: 22 },
  { name: "Spyware", value: 17 },
  { name: "Adware", value: 13 },
  { name: "PUP", value: 10 },
];

export const detectionEngineRadar = [
  { metric: "Precision", value: 92 },
  { metric: "Recall", value: 88 },
  { metric: "F1 Score", value: 90 },
  { metric: "Speed", value: 76 },
  { metric: "Coverage", value: 84 },
  { metric: "Low False+", value: 81 },
];

export const threatTrend = [
  { date: "Jul 28", critical: 12, high: 24, medium: 40 },
  { date: "Jul 29", critical: 18, high: 30, medium: 38 },
  { date: "Jul 30", critical: 9, high: 21, medium: 45 },
  { date: "Jul 31", critical: 22, high: 34, medium: 52 },
  { date: "Aug 1", critical: 15, high: 28, medium: 41 },
  { date: "Aug 2", critical: 27, high: 39, medium: 60 },
  { date: "Aug 3", critical: 19, high: 26, medium: 33 },
];

// Hour-of-day x day-of-week scan intensity, used by the heat map
export const scanHeatmap: number[][] = Array.from({ length: 7 }).map(() =>
  Array.from({ length: 24 }).map(() => Math.floor(Math.random() * 100))
);
