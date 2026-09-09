import { Component, ErrorInfo, ReactNode } from "react";
import { ShieldAlert } from "lucide-react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("ThreatLens UI error:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-background px-4">
          <div className="glass-panel max-w-md w-full p-8 text-center">
            <ShieldAlert className="h-10 w-10 text-severity-critical mx-auto mb-4" />
            <h1 className="font-display text-lg font-semibold mb-2">Something went wrong</h1>
            <p className="text-sm text-muted mb-6">
              An unexpected error occurred while rendering the dashboard. Try reloading the page.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="h-10 px-5 rounded-lg bg-gradient-to-r from-accent-blue to-accent-cyan text-slate-950 font-medium text-sm"
            >
              Reload
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
