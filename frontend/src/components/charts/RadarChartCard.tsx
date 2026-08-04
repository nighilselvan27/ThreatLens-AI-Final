import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, Tooltip } from "recharts";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";

export default function RadarChartCard({
  title,
  data,
}: {
  title: string;
  data: { metric: string; value: number }[];
}) {
  return (
    <Card className="h-[340px]">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <ResponsiveContainer width="100%" height="85%">
        <RadarChart data={data}>
          <PolarGrid stroke="rgba(148,163,184,0.15)" />
          <PolarAngleAxis dataKey="metric" stroke="#64748b" fontSize={11} />
          <PolarRadiusAxis stroke="rgba(148,163,184,0.15)" fontSize={10} tick={false} />
          <Radar dataKey="value" stroke="#a855f7" fill="#a855f7" fillOpacity={0.35} />
          <Tooltip
            contentStyle={{
              backgroundColor: "#131a2a",
              border: "1px solid rgba(148,163,184,0.15)",
              borderRadius: "10px",
              fontSize: "12px",
            }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </Card>
  );
}
