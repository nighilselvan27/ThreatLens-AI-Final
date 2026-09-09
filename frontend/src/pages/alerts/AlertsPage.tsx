import { useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { BellRing, CheckCheck, Trash2, Info, AlertTriangle, ShieldAlert } from "lucide-react";
import { useAppDispatch, useAppSelector } from "@/redux/hooks";
import { fetchAlerts, markAlertAsRead, deleteAlert } from "@/redux/slices/alertsSlice";
import { Card } from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import { SEVERITY_CONFIG } from "@/constants/severity";
import { Severity } from "@/types/threat.types";
import { timeAgo } from "@/utils/formatters";

const FILTERS: (Severity | "all" | "unread")[] = ["all", "unread", "critical", "high", "medium", "low", "info"];

export default function AlertsPage() {
  const dispatch = useAppDispatch();
  const { items } = useAppSelector((s) => s.alerts);
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>("all");

  useEffect(() => {
    dispatch(fetchAlerts());
  }, [dispatch]);

  const unreadCount = items.filter((a) => !a.isRead).length;

  const filtered = useMemo(() => {
    if (filter === "all") return items;
    if (filter === "unread") return items.filter((a) => !a.isRead);
    return items.filter((a) => a.severity === filter);
  }, [items, filter]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="font-display text-xl font-semibold text-slate-100 flex items-center gap-2">
            Security Alerts
            {unreadCount > 0 && <Badge severity="critical">{unreadCount} unread</Badge>}
          </h1>
          <p className="text-sm text-muted mt-1">Real-time notifications from the detection engine.</p>
        </div>
      </div>

      <div className="flex gap-1.5 flex-wrap">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-2 rounded-lg text-xs font-medium capitalize border transition-colors ${
              filter === f
                ? "bg-accent-cyan/10 border-accent-cyan/40 text-accent-cyan"
                : "border-border text-slate-400 hover:text-slate-200"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      <Card>
        <div className="space-y-2">
          <AnimatePresence initial={false}>
            {filtered.map((alert) => {
              const config = SEVERITY_CONFIG[alert.severity];
              return (
                <motion.div
                  key={alert.id}
                  layout
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className={`flex items-start gap-3 rounded-xl border p-4 ${
                    alert.isRead ? "border-white/5 bg-white/[0.01]" : `${config.border} ${config.bg}`
                  }`}
                >
                  <div className={`h-8 w-8 rounded-lg flex items-center justify-center shrink-0 ${config.bg}`}>
                    {alert.severity === "critical" ? (
                      <ShieldAlert className={`h-4 w-4 ${config.color}`} />
                    ) : alert.severity === "info" ? (
                      <Info className={`h-4 w-4 ${config.color}`} />
                    ) : (
                      <AlertTriangle className={`h-4 w-4 ${config.color}`} />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="text-sm font-medium text-slate-100">{alert.title}</p>
                      <Badge severity={alert.severity} />
                      {!alert.isRead && <span className="h-1.5 w-1.5 rounded-full bg-accent-cyan" />}
                    </div>
                    <p className="text-sm text-slate-400 mt-1">{alert.message}</p>
                    <p className="text-xs text-muted mt-1.5">
                      {alert.source} · {timeAgo(alert.createdAt)}
                    </p>
                  </div>
                  <div className="flex gap-1 shrink-0">
                    {!alert.isRead && (
                      <button
                        onClick={() => dispatch(markAlertAsRead(alert.id))}
                        title="Mark as read"
                        className="h-8 w-8 flex items-center justify-center rounded-lg text-slate-400 hover:text-accent-cyan hover:bg-white/5"
                      >
                        <CheckCheck className="h-4 w-4" />
                      </button>
                    )}
                    <button
                      onClick={() => dispatch(deleteAlert(alert.id))}
                      title="Delete alert"
                      className="h-8 w-8 flex items-center justify-center rounded-lg text-slate-400 hover:text-severity-critical hover:bg-white/5"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
          {filtered.length === 0 && (
            <div className="text-center py-12">
              <BellRing className="h-8 w-8 text-slate-700 mx-auto mb-3" />
              <p className="text-sm text-muted">No alerts match this filter.</p>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
