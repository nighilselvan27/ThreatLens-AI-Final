import { Severity } from "./threat.types";

export interface Alert {
  id: string;
  title: string;
  message: string;
  severity: Severity;
  isRead: boolean;
  createdAt: string;
  source: string;
}
