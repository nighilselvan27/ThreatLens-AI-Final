import { Link } from "react-router-dom";
import { ShieldQuestion } from "lucide-react";
import Button from "@/components/ui/Button";
import { ROUTES } from "@/constants/routes";

export default function NotFoundPage() {
  return (
    <div className="min-h-screen bg-background grid-bg flex items-center justify-center px-4">
      <div className="glass-panel max-w-md w-full p-8 text-center">
        <ShieldQuestion className="h-10 w-10 text-accent-cyan mx-auto mb-4" />
        <h1 className="font-display text-3xl font-semibold mb-2">404</h1>
        <p className="text-sm text-muted mb-6">
          This page doesn't exist or may have been moved. Head back to your dashboard.
        </p>
        <Link to={ROUTES.DASHBOARD}>
          <Button>Return to Dashboard</Button>
        </Link>
      </div>
    </div>
  );
}
