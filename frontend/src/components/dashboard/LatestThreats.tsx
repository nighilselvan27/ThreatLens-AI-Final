import { Link } from "react-router-dom";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import { Bug, ChevronRight } from "lucide-react";
import { Threat } from "@/types/threat.types";
import { timeAgo } from "@/utils/formatters";

export default function LatestThreats({ threats }: { threats: Threat[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Latest Threats</CardTitle>
        <Bug className="h-4 w-4 text-muted" />
      </CardHeader>
      <ul className="space-y-1">
        {threats.slice(0, 5).map((t) => (
          <li key={t.id}>
            <Link
              to={`/threats/${t.id}`}
              className="flex items-center justify-between gap-3 py-2.5 px-2 -mx-2 rounded-lg hover:bg-white/5 transition-colors group"
            >
              <div className="min-w-0">
                <p className="text-sm text-slate-200 truncate">{t.threatName}</p>
                <p className="text-xs text-muted mt-0.5">
                  {t.threatFamily} · {timeAgo(t.detectionTime)}
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <Badge severity={t.severity} />
                <ChevronRight className="h-4 w-4 text-slate-600 group-hover:text-accent-cyan transition-colors" />
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </Card>
  );
}
