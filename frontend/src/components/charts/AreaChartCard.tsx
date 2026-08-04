import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";

export default function AreaChartCard({
  title,
  data,
  areaKey,
  xKey,
  color = "#22d3ee",
}: {
  title: string;
  data: any[];
  areaKey: string;
  xKey: string;
  color?: string;
}) {
  return (
    <Card className="h-[340px]">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <ResponsiveContainer width="100%" height="85%">
        <AreaChart data={data} margin={{ top: 4, right: 8, left: -12, bottom: 0 }}>
          <defs>
            <linearGradient id={`grad-${areaKey}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.4} />
              <stop offset="95%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.08)" />
          <XAxis dataKey={xKey} stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
          <YAxis stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
          <Tooltip
            contentStyle={{
              backgroundColor: "#131a2a",
              border: "1px solid rgba(148,163,184,0.15)",
              borderRadius: "10px",
              fontSize: "12px",
            }}
          />
          <Area type="monotone" dataKey={areaKey} stroke={color} strokeWidth={2} fill={`url(#grad-${areaKey})`} />
        </AreaChart>
      </ResponsiveContainer>
    </Card>
  );
}
