import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { cn } from "@/utils/cn";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function intensityColor(v: number) {
  if (v > 80) return "bg-accent-cyan";
  if (v > 60) return "bg-accent-cyan/70";
  if (v > 40) return "bg-accent-blue/60";
  if (v > 20) return "bg-accent-blue/30";
  return "bg-white/5";
}

export default function HeatMapCard({ title, data }: { title: string; data: number[][] }) {
  return (
    <Card className="col-span-full">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <div className="overflow-x-auto">
        <div className="min-w-[720px]">
          <div className="grid grid-cols-[48px_repeat(24,minmax(0,1fr))] gap-1 mb-1">
            <div />
            {Array.from({ length: 24 }).map((_, h) => (
              <span key={h} className="text-[10px] text-slate-600 text-center">
                {h % 3 === 0 ? h : ""}
              </span>
            ))}
          </div>
          {data.map((row, r) => (
            <div key={r} className="grid grid-cols-[48px_repeat(24,minmax(0,1fr))] gap-1 mb-1">
              <span className="text-xs text-slate-500 flex items-center">{DAYS[r]}</span>
              {row.map((val, c) => (
                <div
                  key={c}
                  title={`${DAYS[r]} ${c}:00 — ${val} scans`}
                  className={cn("h-4 rounded-sm transition-colors", intensityColor(val))}
                />
              ))}
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}
