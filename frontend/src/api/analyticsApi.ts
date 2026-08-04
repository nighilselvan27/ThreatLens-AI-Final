import {
  monthlyThreatDetection,
  weeklyUploads,
  threatLevelDistribution,
  topMalwareFamilies,
  riskScoreDistribution,
  classificationResults,
  detectionEngineRadar,
  threatTrend,
  scanHeatmap,
} from "@/data/analyticsData";
import { dashboardStats, recentActivity, recentScans } from "@/data/dashboardData";

export const analyticsApi = {
  getAnalyticsBundle: async () => {
    await new Promise((r) => setTimeout(r, 400));
    return {
      monthlyThreatDetection,
      weeklyUploads,
      threatLevelDistribution,
      topMalwareFamilies,
      riskScoreDistribution,
      classificationResults,
      detectionEngineRadar,
      threatTrend,
      scanHeatmap,
    };
  },
  getDashboardBundle: async () => {
    await new Promise((r) => setTimeout(r, 300));
    return { stats: dashboardStats, recentActivity, recentScans };
  },
};

