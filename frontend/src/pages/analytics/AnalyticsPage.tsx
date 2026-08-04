import { useEffect } from "react";
import { useAppDispatch, useAppSelector } from "@/redux/hooks";
import { fetchAnalytics } from "@/redux/slices/analyticsSlice";
import LineChartCard from "@/components/charts/LineChartCard";
import AreaChartCard from "@/components/charts/AreaChartCard";
import BarChartCard from "@/components/charts/BarChartCard";
import PieChartCard from "@/components/charts/PieChartCard";
import RadarChartCard from "@/components/charts/RadarChartCard";
import HeatMapCard from "@/components/charts/HeatMapCard";
import Skeleton from "@/components/ui/Skeleton";

export default function AnalyticsPage() {
  const dispatch = useAppDispatch();
  const { data, status } = useAppSelector((s) => s.analytics);

  useEffect(() => {
    dispatch(fetchAnalytics());
  }, [dispatch]);

  if (status === "loading" || !data) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-[340px]" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-xl font-semibold text-slate-100">Threat Analytics</h1>
        <p className="text-sm text-muted mt-1">Malware statistics, classification results, and detection trends.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <LineChartCard
          title="Threat Trend (7 Days)"
          data={data.threatTrend}
          xKey="date"
          lines={[
            { key: "critical", color: "#f43f5e", name: "Critical" },
            { key: "high", color: "#fb923c", name: "High" },
            { key: "medium", color: "#facc15", name: "Medium" },
          ]}
        />
        <AreaChartCard title="Monthly Malware Detections" data={data.monthlyThreatDetection} xKey="month" areaKey="malware" color="#22d3ee" />
        <BarChartCard title="Weekly Upload Statistics" data={data.weeklyUploads} xKey="day" barKey="uploads" color="#3b82f6" />
        <PieChartCard title="Threat Level Distribution" data={data.threatLevelDistribution} />
        <BarChartCard
          title="Top Malware Families"
          data={data.topMalwareFamilies}
          xKey="family"
          barKey="detections"
          layout="vertical"
          colors={["#f43f5e", "#fb923c", "#a855f7", "#3b82f6", "#22d3ee", "#34d399"]}
        />
        <BarChartCard title="Risk Score Distribution" data={data.riskScoreDistribution} xKey="range" barKey="count" color="#a855f7" />
        <PieChartCard title="Classification Results" data={data.classificationResults} />
        <RadarChartCard title="Detection Engine Performance" data={data.detectionEngineRadar} />
      </div>

      <HeatMapCard title="Scan Intensity Heat Map (day × hour)" data={data.scanHeatmap} />
    </div>
  );
}
