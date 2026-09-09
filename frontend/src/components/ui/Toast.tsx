import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, Info, AlertTriangle, XCircle, X } from "lucide-react";
import { useAppDispatch, useAppSelector } from "@/redux/hooks";
import { removeToast, ToastItem } from "@/redux/slices/uiSlice";
import { useEffect } from "react";

const ICONS = {
  success: <CheckCircle2 className="h-5 w-5 text-severity-low" />,
  error: <XCircle className="h-5 w-5 text-severity-critical" />,
  warning: <AlertTriangle className="h-5 w-5 text-severity-medium" />,
  info: <Info className="h-5 w-5 text-accent-cyan" />,
};

function ToastCard({ id, title, description, variant }: ToastItem) {
  const dispatch = useAppDispatch();

  useEffect(() => {
    const t = setTimeout(() => dispatch(removeToast(id)), 5000);
    return () => clearTimeout(t);
  }, [id, dispatch]);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: 40 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 40 }}
      className="glass-panel w-80 p-4 flex items-start gap-3"
    >
      {ICONS[variant as keyof typeof ICONS]}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-slate-100">{title}</p>
        {description && <p className="text-xs text-muted mt-0.5">{description}</p>}
      </div>
      <button onClick={() => dispatch(removeToast(id))} className="text-slate-500 hover:text-white">
        <X className="h-4 w-4" />
      </button>
    </motion.div>
  );
}

export default function ToastViewport() {
  const toasts = useAppSelector((s) => s.ui.toasts);

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2">
      <AnimatePresence>
        {toasts.map((t) => (
          <ToastCard key={t.id} {...t} />
        ))}
      </AnimatePresence>
    </div>
  );
}
