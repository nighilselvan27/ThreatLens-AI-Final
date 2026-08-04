import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import { FileSearch } from "lucide-react";

export default function RecentScans({
  items,
}: {
  items: readonly { id: string; fileName: string; riskLevel: string; time: string }[];
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Scans</CardTitle>
        <FileSearch className="h-4 w-4 text-muted" />
      </CardHeader>
      <ul className="space-y-3">
        {items.map((item) => (
          <li key={item.id} className="flex items-center justify-between gap-3 text-sm">
            <div className="min-w-0">
              <p className="text-slate-200 truncate font-mono text-xs">{item.fileName}</p>
              <p className="text-xs text-muted mt-0.5">{item.time}</p>
            </div>
            <Badge severity={item.riskLevel as any} />
          </li>
        ))}
      </ul>
    </Card>
  );
}
