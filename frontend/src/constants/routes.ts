export const ROUTES = {
  LOGIN: "/login",
  DASHBOARD: "/",
  UPLOAD: "/upload",
  REPORTS: "/reports",
  ANALYTICS: "/analytics",
  ALERTS: "/alerts",
  THREAT_DETAILS: "/threats/:id",
  threatDetails: (id: string) => `/threats/${id}`,
  SETTINGS: "/settings",
} as const;
