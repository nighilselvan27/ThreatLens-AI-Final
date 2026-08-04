import { cn } from "@/utils/cn";

export default function ProgressBar({
  value,
  className,
  showLabel = false,
}: {
  value: number;
  className?: string;
  showLabel?: boolean;
}) {
  return (
    <div className={cn("w-full", className)}>
      <div className="h-1.5 w-full rounded-full bg-white/5 overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-to-r from-accent-blue to-accent-cyan transition-all duration-300"
          style={{ width: `${value}%` }}
        />
      </div>
      {showLabel && <span className="text-xs text-muted mt-1 block">{value}%</span>}
    </div>
  );
}
