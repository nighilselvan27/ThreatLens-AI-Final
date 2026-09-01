import { Link } from "react-router-dom";
import { ShieldOff } from "lucide-react";
import { useAppSelector } from "@/redux/hooks";
import { ROLE_LABELS } from "@/constants/roles";
import { ROUTES } from "@/constants/routes";

export default function AccessDeniedPage() {
  const user = useAppSelector((s) => s.auth.user);

  return (
    <div className="flex items-center justify-center py-20">
      <div className="glass-panel max-w-md w-full p-8 text-center">
        <ShieldOff className="h-10 w-10 text-severity-critical mx-auto mb-4" />
        <h1 className="font-display text-lg font-semibold mb-2">Access Restricted</h1>
        <p className="text-sm text-muted mb-2">
          Your account role{user ? ` (${ROLE_LABELS[user.role]})` : ""} doesn't have permission
          to view this page.
        </p>
        <p className="text-xs text-slate-500 mb-6">
          Contact an Administrator if you believe this is incorrect.
        </p>
        <Link
          to={ROUTES.DASHBOARD}
          className="inline-flex items-center justify-center gap-2 rounded-lg font-medium h-10 px-5 text-sm bg-gradient-to-r from-accent-blue to-accent-cyan text-slate-950 hover:shadow-glow hover:brightness-110 transition-all"
        >
          Return to Dashboard
        </Link>
      </div>
    </div>
  );
}