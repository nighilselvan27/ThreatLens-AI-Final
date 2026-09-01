import { lazy, Suspense } from "react";
import { Routes, Route } from "react-router-dom";
import DashboardLayout from "@/layouts/DashboardLayout";
import AuthLayout from "@/layouts/AuthLayout";
import ProtectedRoute from "@/components/layout/ProtectedRoute";
import RequireRole from "@/components/layout/RequireRole";
import Skeleton from "@/components/ui/Skeleton";
import { ROUTES } from "@/constants/routes";

const LoginPage = lazy(() => import("@/pages/auth/LoginPage"));
const DashboardPage = lazy(() => import("@/pages/dashboard/DashboardPage"));
const UploadPage = lazy(() => import("@/pages/upload/UploadPage"));
const ReportsPage = lazy(() => import("@/pages/reports/ReportsPage"));
const AnalyticsPage = lazy(() => import("@/pages/analytics/AnalyticsPage"));
const AlertsPage = lazy(() => import("@/pages/alerts/AlertsPage"));
const ThreatDetailsPage = lazy(() => import("@/pages/threats/ThreatDetailsPage"));
const SettingsPage = lazy(() => import("@/pages/settings/SettingsPage"));
const AccessDeniedPage = lazy(() => import("@/pages/AccessDeniedPage"));
const NotFoundPage = lazy(() => import("@/pages/NotFoundPage"));

function PageFallback() {
  return (
    <div className="p-6 space-y-4">
      <Skeleton className="h-8 w-56" />
      <Skeleton className="h-40" />
    </div>
  );
}

export default function AppRoutes() {
  return (
    <Suspense fallback={<PageFallback />}>
      <Routes>
        {/* Public routes */}
        <Route element={<AuthLayout />}>
          <Route path={ROUTES.LOGIN} element={<LoginPage />} />
        </Route>

        {/* Protected routes — must be logged in AND have a permitted role */}
        <Route element={<ProtectedRoute />}>
          <Route element={<DashboardLayout />}>
            <Route
              path={ROUTES.DASHBOARD}
              element={
                <RequireRole page="dashboard">
                  <DashboardPage />
                </RequireRole>
              }
            />
            <Route
              path={ROUTES.UPLOAD}
              element={
                <RequireRole page="upload">
                  <UploadPage />
                </RequireRole>
              }
            />
            <Route
              path={ROUTES.REPORTS}
              element={
                <RequireRole page="reports">
                  <ReportsPage />
                </RequireRole>
              }
            />
            <Route
              path={ROUTES.ANALYTICS}
              element={
                <RequireRole page="analytics">
                  <AnalyticsPage />
                </RequireRole>
              }
            />
            <Route
              path={ROUTES.ALERTS}
              element={
                <RequireRole page="alerts">
                  <AlertsPage />
                </RequireRole>
              }
            />
            <Route
              path={ROUTES.THREAT_DETAILS}
              element={
                <RequireRole page="threatDetails">
                  <ThreatDetailsPage />
                </RequireRole>
              }
            />
            <Route
              path={ROUTES.SETTINGS}
              element={
                <RequireRole page="settings">
                  <SettingsPage />
                </RequireRole>
              }
            />
            <Route path="/access-denied" element={<AccessDeniedPage />} />
          </Route>
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  );
}