import { AnimatePresence, motion } from "framer-motion";
import { NavLink, useNavigate } from "react-router-dom";
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
  X,
} from "lucide-react";
import { useAppDispatch, useAppSelector } from "@/redux/hooks";
import { logoutUser } from "@/redux/slices/authSlice";
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

export default function MobileNav({ open, onClose }: { open: boolean; onClose: () => void }) {
  const user = useAppSelector((s) => s.auth.user);
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const visibleNavItems = NAV_ITEMS.filter((item) => canAccess(user?.role, item.page));

  async function handleLogout() {
    await dispatch(logoutUser());
    navigate(ROUTES.LOGIN);
    onClose();
  }

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50 md:hidden">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={onClose}
          />
          <motion.aside
            initial={{ x: "-100%" }}
            animate={{ x: 0 }}
            exit={{ x: "-100%" }}
            transition={{ type: "tween", duration: 0.2 }}
            className="relative h-full w-72 max-w-[80vw] bg-background-surface border-r border-border flex flex-col"
          >
            <div className="flex items-center justify-between h-16 px-4 border-b border-border">
              <div className="flex items-center gap-2.5">
                <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-accent-cyan to-accent-purple flex items-center justify-center shrink-0">
                  <ShieldHalf className="h-4.5 w-4.5 text-slate-950" />
                </div>
                <span className="font-display font-semibold text-slate-100 tracking-tight">
                  ThreatLens<span className="text-accent-cyan">.AI</span>
                </span>
              </div>
              <button onClick={onClose} aria-label="Close menu" className="text-slate-400 hover:text-white">
                <X className="h-5 w-5" />
              </button>
            </div>

            <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
              {visibleNavItems.map((item) => (
                <NavLink
                  key={item.label}
                  to={item.to}
                  onClick={onClose}
                  className={({ isActive }) =>
                    `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors border ${
                      isActive
                        ? "bg-accent-cyan/10 text-accent-cyan border-accent-cyan/20"
                        : "text-slate-400 hover:text-slate-100 hover:bg-white/5 border-transparent"
                    }`
                  }
                >
                  <item.icon className="h-[18px] w-[18px] shrink-0" />
                  <span className="truncate">{item.label}</span>
                </NavLink>
              ))}
            </nav>

            <div className="p-3 border-t border-border">
              <button
                onClick={handleLogout}
                className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-400 hover:text-severity-critical hover:bg-severity-critical/10 transition-colors"
              >
                <LogOut className="h-[18px] w-[18px]" />
                <span>Logout</span>
              </button>
            </div>
          </motion.aside>
        </div>
      )}
    </AnimatePresence>
  );
}