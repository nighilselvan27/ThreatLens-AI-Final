import { Outlet } from "react-router-dom";
import { ShieldHalf } from "lucide-react";

export default function AuthLayout() {
  return (
    <div className="min-h-screen bg-background grid-bg flex items-center justify-center px-4 relative overflow-hidden">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 h-96 w-96 bg-accent-blue/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-0 right-1/4 h-96 w-96 bg-accent-purple/10 rounded-full blur-[120px]" />
      </div>
      <div className="relative w-full max-w-md">
        <div className="flex items-center justify-center gap-2.5 mb-8">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-accent-cyan to-accent-purple flex items-center justify-center">
            <ShieldHalf className="h-5 w-5 text-slate-950" />
          </div>
          <span className="font-display text-xl font-semibold tracking-tight">
            ThreatLens<span className="text-accent-cyan">.AI</span>
          </span>
        </div>
        <Outlet />
      </div>
    </div>
  );
}
