import { NavLink } from "react-router-dom";
import {
  ShieldHalf,
  LayoutDashboard,
  UploadCloud,
  FileBarChart2,
  LineChart,
  BellRing,
  Bug,
  Settings,
  LogOut,
  ChevronsLeft,
  ChevronsRight,
} from "lucide-react";
import { cn } from "@/utils/cn";
import { useAppDispatch, useAppSelector } from "@/redux/hooks";
import { toggleSidebar } from "@/redux/slices/uiSlice";
import { logoutUser } from "@/redux/slices/authSlice";
import { useNavigate } from "react-router-dom";
import { ROUTES } from "@/constants/routes";
import { canAccess, PageKey } from "@/constants/roles";

const NAV_ITEMS: { to: string; label: string; icon: typeof LayoutDashboard; page: PageKey }[] = [
  { to: ROUTES.DASHBOARD, label: "Dashboard", icon: LayoutDashboard, page: "dashboard" },
  { to: ROUTES.UPLOAD, label: "Upload", icon: UploadCloud, page: "upload" },
  { to: ROUTES.REPORTS, label: "Reports", icon: FileBarChart2, page: "reports" },
  { to: ROUTES.ANALYTICS, label: "Analytics", icon: LineChart, page: "analytics" },
  { to: ROUTES.ALERTS, label: "Alerts", icon: BellRing, page: "alerts" },
  { to: "/threats/thr-1001", label: "Threat Details", icon: Bug, page: "threatDetails" },
  { to: ROUTES.SETTINGS, label: "Settings", icon: Settings, page: "settings" },
];

export default function Sidebar() {
  const collapsed = useAppSelector((s) => s.ui.sidebarCollapsed);
  const user = useAppSelector((s) => s.auth.user);
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  // Sidebar filtering is a convenience (don't show links the user can't
  // use) — it is NOT the security boundary. The actual page-level check
  // happens in RequireRole inside AppRoutes.tsx, so even if someone types
  // a restricted URL directly, they're still blocked.
  const visibleNavItems = NAV_ITEMS.filter((item) => canAccess(user?.role, item.page));

  async function handleLogout() {
    await dispatch(logoutUser());
    navigate(ROUTES.LOGIN);
  }

  return (
    <aside
      className={cn(
        "hidden md:flex flex-col shrink-0 h-screen sticky top-0 border-r border-border bg-background-surface/60 backdrop-blur-xl transition-all duration-300",
        collapsed ? "w-[76px]" : "w-64"
      )}
    >
      <div className="flex items-center gap-2.5 h-16 px-4 border-b border-border">
        <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-accent-cyan to-accent-purple flex items-center justify-center shrink-0">
          <ShieldHalf className="h-4.5 w-4.5 text-slate-950" />
        </div>
        {!collapsed && (
          <span className="font-display font-semibold text-slate-100 tracking-tight">
            ThreatLens<span className="text-accent-cyan">.AI</span>
          </span>
        )}
      </div>

      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
        {visibleNavItems.map((item) => (
          <NavLink
            key={item.label}
            to={item.to}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors group relative",
                isActive
                  ? "bg-accent-cyan/10 text-accent-cyan border border-accent-cyan/20"
                  : "text-slate-400 hover:text-slate-100 hover:bg-white/5 border border-transparent"
              )
            }
          >
            <item.icon className="h-[18px] w-[18px] shrink-0" />
            {!collapsed && <span className="truncate">{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      <div className="p-3 border-t border-border space-y-1">
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-400 hover:text-severity-critical hover:bg-severity-critical/10 transition-colors"
        >
          <LogOut className="h-[18px] w-[18px]" />
          {!collapsed && <span>Logout</span>}
        </button>
        <button
          onClick={() => dispatch(toggleSidebar())}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-slate-500 hover:text-slate-200 hover:bg-white/5 transition-colors"
        >
          {collapsed ? <ChevronsRight className="h-[18px] w-[18px]" /> : <ChevronsLeft className="h-[18px] w-[18px]" />}
          {!collapsed && <span>Collapse</span>}
        </button>
      </div>
    </aside>
  );
}