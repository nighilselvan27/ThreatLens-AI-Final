import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { SEVERITY_CONFIG } from "@/constants/severity";
import { Severity } from "@/types/threat.types";

export default function ThreatSeveritySummary({ counts }: { counts: Record<Severity, number> }) {
  const total = Object.values(counts).reduce((a, b) => a + b, 0) || 1;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Threat Severity Summary</CardTitle>
      </CardHeader>
      <div className="space-y-3">
        {(Object.keys(counts) as Severity[]).map((key) => {
          const config = SEVERITY_CONFIG[key];
          const pct = Math.round((counts[key] / total) * 100);
          return (
            <div key={key}>
              <div className="flex justify-between text-xs mb-1.5">
                <span className={config.color}>{config.label}</span>
                <span className="text-muted">{counts[key]}</span>
              </div>
              <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                <div className={`h-full rounded-full ${config.dot}`} style={{ width: `${pct}%` }} />
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
