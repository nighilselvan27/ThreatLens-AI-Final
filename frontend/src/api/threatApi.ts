import { Threat } from "@/types/threat.types";
import { threats } from "@/data/threatsData";

export const threatApi = {
  getThreats: async (): Promise<Threat[]> => {
    await new Promise((r) => setTimeout(r, 350));
    return threats;
  },
  getThreatById: async (id: string): Promise<Threat | undefined> => {
    await new Promise((r) => setTimeout(r, 300));
    return threats.find((t) => t.id === id);
  },
};
