import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Activity } from "lucide-react";

export default function RecentActivity({
  items,
}: {
  items: { id: string; actor: string; action: string; time: string }[];
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
        <Activity className="h-4 w-4 text-muted" />
      </CardHeader>
      <ul className="space-y-4">
        {items.map((item) => (
          <li key={item.id} className="flex gap-3 text-sm">
            <div className="h-1.5 w-1.5 rounded-full bg-accent-cyan mt-1.5 shrink-0" />
            <div className="min-w-0">
              <p className="text-slate-200">
                <span className="font-medium">{item.actor}</span>{" "}
                <span className="text-slate-400">{item.action}</span>
              </p>
              <p className="text-xs text-muted mt-0.5">{item.time}</p>
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}
