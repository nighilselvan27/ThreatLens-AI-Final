import { useNavigate } from "react-router-dom";
import { UploadCloud, FileBarChart2, BellRing, LineChart } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { ROUTES } from "@/constants/routes";

const ACTIONS = [
  { label: "Scan File", icon: UploadCloud, to: ROUTES.UPLOAD, accent: "text-accent-cyan bg-accent-cyan/10" },
  { label: "View Reports", icon: FileBarChart2, to: ROUTES.REPORTS, accent: "text-accent-blue bg-accent-blue/10" },
  { label: "Check Alerts", icon: BellRing, to: ROUTES.ALERTS, accent: "text-severity-medium bg-severity-medium/10" },
  { label: "Analytics", icon: LineChart, to: ROUTES.ANALYTICS, accent: "text-accent-purple bg-accent-purple/10" },
];

export default function QuickActions() {
  const navigate = useNavigate();
  return (
    <Card>
      <CardHeader>
        <CardTitle>Quick Actions</CardTitle>
      </CardHeader>
      <div className="grid grid-cols-2 gap-3">
        {ACTIONS.map((a) => (
          <button
            key={a.label}
            onClick={() => navigate(a.to)}
            className="flex flex-col items-center gap-2 rounded-xl border border-border p-4 hover:border-accent-cyan/30 hover:bg-white/[0.03] transition-all"
          >
            <div className={`h-9 w-9 rounded-lg flex items-center justify-center ${a.accent}`}>
              <a.icon className="h-4.5 w-4.5" />
            </div>
            <span className="text-xs font-medium text-slate-300">{a.label}</span>
          </button>
        ))}
      </div>
    </Card>
  );
}
