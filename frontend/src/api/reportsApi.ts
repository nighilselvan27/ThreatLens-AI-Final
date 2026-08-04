import { Report } from "@/types/report.types";
import { reports } from "@/data/reportsData";

export const reportsApi = {
  getReports: async (): Promise<Report[]> => {
    await new Promise((r) => setTimeout(r, 400));
    return reports;
  },
  deleteReport: async (id: string): Promise<{ id: string }> => {
    await new Promise((r) => setTimeout(r, 300));
    return { id };
  },
};
