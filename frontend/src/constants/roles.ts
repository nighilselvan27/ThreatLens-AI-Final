import { User } from "@/types/auth.types";

export type Role = User["role"];

export const ROLES: Role[] = [
  "security_analyst",
  "soc_team_member",
  "administrator",
  "researcher",
];

export const ROLE_LABELS: Record<Role, string> = {
  security_analyst: "Security Analyst",
  soc_team_member: "SOC Team Member",
  administrator: "Administrator",
  researcher: "Researcher",
};

export const PAGE_ACCESS = {
  dashboard: ["security_analyst", "soc_team_member", "administrator", "researcher"],
  upload: ["security_analyst", "administrator", "researcher"],
  reports: ["security_analyst", "soc_team_member", "administrator", "researcher"],
  analytics: ["administrator", "researcher"],
  alerts: ["security_analyst", "soc_team_member", "administrator"],
  threatDetails: ["security_analyst", "soc_team_member", "administrator"],
  settings: ["security_analyst", "soc_team_member", "administrator", "researcher"],
} as const satisfies Record<string, Role[]>;

export type PageKey = keyof typeof PAGE_ACCESS;

export function canAccess(role: Role | undefined, page: PageKey): boolean {
  if (!role) return false;
  return (PAGE_ACCESS[page] as readonly Role[]).includes(role);
}