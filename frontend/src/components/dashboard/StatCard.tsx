import { motion } from "framer-motion";
import { LucideIcon } from "lucide-react";
import { cn } from "@/utils/cn";
import { formatNumber } from "@/utils/formatters";

export default function StatCard({
  label,
  value,
  icon: Icon,
  trend,
  accent = "cyan",
  suffix,
}: {
  label: string;
  value: number;
  icon: LucideIcon;
  trend?: { value: number; positive: boolean };
  accent?: "cyan" | "blue" | "purple" | "critical" | "low";
  suffix?: string;
}) {
  const accentMap = {
    cyan: "from-accent-cyan/20 to-accent-cyan/5 text-accent-cyan",
    blue: "from-accent-blue/20 to-accent-blue/5 text-accent-blue",
    purple: "from-accent-purple/20 to-accent-purple/5 text-accent-purple",
    critical: "from-severity-critical/20 to-severity-critical/5 text-severity-critical",
    low: "from-severity-low/20 to-severity-low/5 text-severity-low",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="glass-card p-5 relative overflow-hidden"
    >
      <div className={cn("absolute -top-6 -right-6 h-20 w-20 rounded-full bg-gradient-to-br blur-xl", accentMap[accent])} />
      <div className="flex items-start justify-between relative">
        <div>
          <p className="text-xs text-muted font-medium mb-1.5">{label}</p>
          <p className="font-display text-2xl font-semibold text-slate-100">
            {formatNumber(value)}
            {suffix}
          </p>
          {trend && (
            <p className={cn("text-xs mt-1.5 font-medium", trend.positive ? "text-severity-low" : "text-severity-critical")}>
              {trend.positive ? "▲" : "▼"} {Math.abs(trend.value)}% vs last week
            </p>
          )}
        </div>
        <div className={cn("h-10 w-10 rounded-lg bg-gradient-to-br flex items-center justify-center shrink-0", accentMap[accent])}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </motion.div>
  );
}
