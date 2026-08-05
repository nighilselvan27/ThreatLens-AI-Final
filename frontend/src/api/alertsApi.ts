import { Alert } from "@/types/alert.types";
import { alerts } from "@/data/alertsData";

export const alertsApi = {
  getAlerts: async (): Promise<Alert[]> => {
    await new Promise((r) => setTimeout(r, 350));
    return alerts;
  },
  markAsRead: async (id: string): Promise<{ id: string }> => {
    await new Promise((r) => setTimeout(r, 150));
    return { id };
  },
  deleteAlert: async (id: string): Promise<{ id: string }> => {
    await new Promise((r) => setTimeout(r, 150));
    return { id };
  },
};
