import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";

export default function BarChartCard({
  title,
  data,
  barKey,
  xKey,
  color = "#3b82f6",
  colors,
  layout = "horizontal",
}: {
  title: string;
  data: any[];
  barKey: string;
  xKey: string;
  color?: string;
  colors?: string[];
  layout?: "horizontal" | "vertical";
}) {
  return (
    <Card className="h-[340px]">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <ResponsiveContainer width="100%" height="85%">
        <BarChart
          data={data}
          layout={layout}
          margin={{ top: 4, right: 8, left: layout === "vertical" ? 40 : -12, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.08)" />
          {layout === "horizontal" ? (
            <>
              <XAxis dataKey={xKey} stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
            </>
          ) : (
            <>
              <XAxis type="number" stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis dataKey={xKey} type="category" stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} width={90} />
            </>
          )}
          <Tooltip
            contentStyle={{
              backgroundColor: "#131a2a",
              border: "1px solid rgba(148,163,184,0.15)",
              borderRadius: "10px",
              fontSize: "12px",
            }}
            cursor={{ fill: "rgba(148,163,184,0.05)" }}
          />
          <Bar dataKey={barKey} radius={[6, 6, 6, 6]}>
            {data.map((_, i) => (
              <Cell key={i} fill={colors ? colors[i % colors.length] : color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
}
