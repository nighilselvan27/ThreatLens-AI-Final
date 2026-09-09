import { useEffect } from "react";
import { FileCheck2, Bug, ShieldCheck, Gauge, ScanLine, BellRing } from "lucide-react";
import { useAppDispatch, useAppSelector } from "@/redux/hooks";
import { fetchDashboardData } from "@/redux/slices/dashboardSlice";
import { fetchAlerts } from "@/redux/slices/alertsSlice";
import StatCard from "@/components/dashboard/StatCard";
import RecentActivity from "@/components/dashboard/RecentActivity";
import RecentScans from "@/components/dashboard/RecentScans";
import LatestThreats from "@/components/dashboard/LatestThreats";
import QuickActions from "@/components/dashboard/QuickActions";
import ThreatSeveritySummary from "@/components/dashboard/ThreatSeveritySummary";
import Skeleton from "@/components/ui/Skeleton";
import { threats } from "@/data/threatsData";
import { Severity } from "@/types/threat.types";

export default function DashboardPage() {
  const dispatch = useAppDispatch();
  const { stats, recentActivity, recentScans, status } = useAppSelector((s) => s.dashboard);

  useEffect(() => {
    dispatch(fetchDashboardData());
    dispatch(fetchAlerts());
  }, [dispatch]);

  const severityCounts = threats.reduce(
    (acc, t) => {
      acc[t.severity] += 1;
      return acc;
    },
    { critical: 0, high: 0, medium: 0, low: 0, info: 0 } as Record<Severity, number>
  );

  if (status === "loading" || !stats) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-28" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-xl font-semibold text-slate-100">Security Overview</h1>
        <p className="text-sm text-muted mt-1">Real-time malware detection and threat analytics.</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard label="Total Files Scanned" value={stats.totalFilesScanned} icon={FileCheck2} accent="blue" trend={{ value: 8, positive: true }} />
        <StatCard label="Malware Detected" value={stats.malwareDetected} icon={Bug} accent="critical" trend={{ value: 3, positive: false }} />
        <StatCard label="Safe Files" value={stats.safeFiles} icon={ShieldCheck} accent="low" trend={{ value: 5, positive: true }} />
        <StatCard label="Threat Score" value={stats.threatScore} suffix="/100" icon={Gauge} accent="purple" />
        <StatCard label="Today's Scans" value={stats.todaysScans} icon={ScanLine} accent="cyan" />
        <StatCard label="Active Alerts" value={stats.activeAlerts} icon={BellRing} accent="critical" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <LatestThreats threats={threats} />
          <RecentActivity items={recentActivity} />
        </div>
        <div className="space-y-6">
          <QuickActions />
          <ThreatSeveritySummary counts={severityCounts} />
          <RecentScans items={recentScans} />
        </div>
      </div>
    </div>
  );
}
