import { useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Link, useNavigate } from "react-router-dom";
import { Eye, EyeOff, Mail, Lock, ShieldCheck, ArrowRight } from "lucide-react";
import { loginSchema, LoginFormValues } from "@/utils/validators";
import { useAppDispatch, useAppSelector } from "@/redux/hooks";
import { loginUser, clearAuthError } from "@/redux/slices/authSlice";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import { useToast } from "@/hooks/useToast";
import { ROUTES } from "@/constants/routes";

// Demo account picker — like a "choose an account" list. Purely a UI
// convenience for testing/demoing RBAC; selecting one just fills in the
// email (and a default password) field. It does NOT log the user in by
// itself and does NOT let anyone pick their own role — the actual role is
// still looked up from the email in authApi.ts, exactly as before.
const DEMO_ACCOUNTS = [
  { email: "analyst@example.com", label: "Security Analyst", dotClass: "bg-accent-cyan" },
  { email: "soc@example.com", label: "SOC Team Member", dotClass: "bg-accent-blue" },
  { email: "admin@example.com", label: "Administrator", dotClass: "bg-accent-purple" },
  { email: "researcher@example.com", label: "Researcher", dotClass: "bg-severity-medium" },
];
const DEMO_PASSWORD = "password123";

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [showAccountPicker, setShowAccountPicker] = useState(false);
  const pickerRef = useRef<HTMLDivElement>(null);
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { status, error } = useAppSelector((s) => s.auth);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "", rememberMe: false },
  });

  // Close the picker when clicking anywhere outside it.
  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (pickerRef.current && !pickerRef.current.contains(e.target as Node)) {
        setShowAccountPicker(false);
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  function handleSelectDemoAccount(account: (typeof DEMO_ACCOUNTS)[number]) {
    setValue("email", account.email, { shouldValidate: true });
    setValue("password", DEMO_PASSWORD, { shouldValidate: true });
    setShowAccountPicker(false);
  }

  async function onSubmit(values: LoginFormValues) {
    dispatch(clearAuthError());
    const result = await dispatch(loginUser(values));
    if (loginUser.fulfilled.match(result)) {
      toast({ title: "Welcome back", description: "Signed in successfully.", variant: "success" });
      navigate(ROUTES.DASHBOARD);
    } else {
      toast({ title: "Login failed", description: "Check your credentials and try again.", variant: "error" });
    }
  }

  return (
    <div className="glass-panel p-8 relative overflow-hidden">
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-accent-cyan/50 to-transparent" />

      <div className="flex items-center gap-2 mb-1">
        <ShieldCheck className="h-4 w-4 text-accent-cyan" />
        <span className="text-xs font-medium text-accent-cyan tracking-wide uppercase">Secure Access</span>
      </div>
      <h1 className="font-display text-2xl font-semibold mb-1.5">Sign in to your workspace</h1>
      <p className="text-sm text-muted mb-7">Monitor threats, review scans, and manage alerts.</p>

      {error && (
        <div className="mb-5 rounded-lg border border-severity-critical/30 bg-severity-critical/10 px-3.5 py-2.5 text-sm text-severity-critical">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <div className="relative" ref={pickerRef}>
          <label className="text-xs font-medium text-slate-400 mb-1.5 block">Email address</label>
          <div className="relative">
            <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            <Input
              type="email"
              placeholder="you@company.com"
              className="pl-10"
              error={errors.email?.message}
              onFocus={() => setShowAccountPicker(true)}
              {...register("email")}
            />
          </div>
          {errors.email && <p className="text-xs text-severity-critical mt-1.5">{errors.email.message}</p>}

          {/* Demo account picker — appears when the email field is focused */}
          {showAccountPicker && (
            <div className="absolute z-20 mt-1.5 w-full glass-panel p-1.5">
              <p className="px-2.5 pt-1.5 pb-2 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                Choose a demo account
              </p>
              {DEMO_ACCOUNTS.map((account) => (
                <button
                  key={account.email}
                  type="button"
                  onMouseDown={(e) => {
                    // onMouseDown fires before the input's onBlur, so the
                    // click registers before the picker would otherwise close.
                    e.preventDefault();
                    handleSelectDemoAccount(account);
                  }}
                  className="flex w-full items-center gap-3 rounded-lg px-2.5 py-2.5 text-left hover:bg-white/5 transition-colors"
                >
                  <span className={`h-2 w-2 rounded-full shrink-0 ${account.dotClass}`} />
                  <span className="min-w-0">
                    <span className="block text-sm text-slate-100">{account.label}</span>
                    <span className="block text-xs text-muted truncate">{account.email}</span>
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-xs font-medium text-slate-400">Password</label>
            <Link to="#" className="text-xs text-accent-cyan hover:text-accent-cyan/80">
              Forgot password?
            </Link>
          </div>
          <div className="relative">
            <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            <Input
              type={showPassword ? "text" : "password"}
              placeholder="••••••••"
              className="pl-10 pr-10"
              error={errors.password?.message}
              {...register("password")}
            />
            <button
              type="button"
              onClick={() => setShowPassword((s) => !s)}
              className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {errors.password && <p className="text-xs text-severity-critical mt-1.5">{errors.password.message}</p>}
        </div>

        <label className="flex items-center gap-2 text-sm text-slate-400">
          <input type="checkbox" className="rounded border-border bg-background-surface accent-accent-cyan" {...register("rememberMe")} />
          Remember me for 30 days
        </label>

        <Button type="submit" className="w-full" size="lg" isLoading={status === "loading"}>
          {status !== "loading" && (
            <>
              Sign in <ArrowRight className="h-4 w-4" />
            </>
          )}
        </Button>
      </form>

      <p className="text-xs text-center text-muted mt-6">
        Click the email field above to pick a demo account · password is filled in automatically
      </p>
    </div>
  );
}