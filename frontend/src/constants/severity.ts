import { Severity } from "@/types/threat.types";

export const SEVERITY_CONFIG: Record<
  Severity,
  { label: string; color: string; bg: string; border: string; dot: string }
> = {
  critical: {
    label: "Critical",
    color: "text-severity-critical",
    bg: "bg-severity-critical/10",
    border: "border-severity-critical/30",
    dot: "bg-severity-critical",
  },
  high: {
    label: "High",
    color: "text-severity-high",
    bg: "bg-severity-high/10",
    border: "border-severity-high/30",
    dot: "bg-severity-high",
  },
  medium: {
    label: "Medium",
    color: "text-severity-medium",
    bg: "bg-severity-medium/10",
    border: "border-severity-medium/30",
    dot: "bg-severity-medium",
  },
  low: {
    label: "Low",
    color: "text-severity-low",
    bg: "bg-severity-low/10",
    border: "border-severity-low/30",
    dot: "bg-severity-low",
  },
  info: {
    label: "Info",
    color: "text-severity-info",
    bg: "bg-severity-info/10",
    border: "border-severity-info/30",
    dot: "bg-severity-info",
  },
};
