import { Bell, Search, Sun, Moon, ChevronDown, User as UserIcon, Settings, LogOut, Menu } from "lucide-react";
import { useAppDispatch, useAppSelector } from "@/redux/hooks";
import { toggleDarkMode } from "@/redux/slices/uiSlice";
import { logoutUser } from "@/redux/slices/authSlice";
import { Dropdown, DropdownItem } from "@/components/ui/Dropdown";
import { useNavigate } from "react-router-dom";
import { ROUTES } from "@/constants/routes";

export default function Navbar({ onMenuClick }: { onMenuClick?: () => void }) {
  const dispatch = useAppDispatch();
  const darkMode = useAppSelector((s) => s.ui.darkMode);
  const user = useAppSelector((s) => s.auth.user);
  const alerts = useAppSelector((s) => s.alerts.items);
  const unreadCount = alerts.filter((a) => !a.isRead).length;
  const navigate = useNavigate();

  async function handleLogout() {
    await dispatch(logoutUser());
    navigate(ROUTES.LOGIN);
  }

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-border bg-background/80 backdrop-blur-xl px-4 md:px-6">
      <button
        onClick={onMenuClick}
        aria-label="Open menu"
        className="md:hidden h-9 w-9 flex items-center justify-center rounded-lg text-slate-400 hover:text-slate-100 hover:bg-white/5 transition-colors shrink-0"
      >
        <Menu className="h-5 w-5" />
      </button>

      <div className="relative flex-1 max-w-md hidden sm:block">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
        <input
          type="search"
          placeholder="Search threats, hashes, files..."
          className="w-full h-10 rounded-lg bg-background-surface border border-border pl-9 pr-3 text-sm placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-accent-cyan/50 focus:border-accent-cyan/50"
        />
      </div>

      <div className="flex items-center gap-2 ml-auto">
        <button
          onClick={() => dispatch(toggleDarkMode())}
          aria-label="Toggle dark mode"
          className="h-9 w-9 flex items-center justify-center rounded-lg text-slate-400 hover:text-slate-100 hover:bg-white/5 transition-colors"
        >
          {darkMode ? <Sun className="h-[18px] w-[18px]" /> : <Moon className="h-[18px] w-[18px]" />}
        </button>

        <button
          onClick={() => navigate(ROUTES.ALERTS)}
          aria-label="Notifications"
          className="relative h-9 w-9 flex items-center justify-center rounded-lg text-slate-400 hover:text-slate-100 hover:bg-white/5 transition-colors"
        >
          <Bell className="h-[18px] w-[18px]" />
          {unreadCount > 0 && (
            <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-severity-critical ring-2 ring-background" />
          )}
        </button>

        <Dropdown
          trigger={
            <button className="flex items-center gap-2 rounded-lg pl-1 pr-2 py-1 hover:bg-white/5 transition-colors">
              <div className="h-8 w-8 rounded-full bg-gradient-to-br from-accent-purple to-accent-blue flex items-center justify-center text-xs font-semibold text-white">
                {user?.name?.charAt(0) ?? "A"}
              </div>
              <span className="hidden sm:block text-sm font-medium text-slate-200">{user?.name ?? "Analyst"}</span>
              <ChevronDown className="h-3.5 w-3.5 text-slate-500" />
            </button>
          }
        >
          <DropdownItem onClick={() => navigate(ROUTES.SETTINGS)}>
            <UserIcon className="h-4 w-4" /> Profile
          </DropdownItem>
          <DropdownItem onClick={() => navigate(ROUTES.SETTINGS)}>
            <Settings className="h-4 w-4" /> Settings
          </DropdownItem>
          <DropdownItem onClick={handleLogout} className="text-severity-critical hover:bg-severity-critical/10">
            <LogOut className="h-4 w-4" /> Logout
          </DropdownItem>
        </Dropdown>
      </div>
    </header>
  );
}