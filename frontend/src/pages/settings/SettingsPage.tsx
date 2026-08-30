import { useAppSelector, useAppDispatch } from "@/redux/hooks";
import { toggleDarkMode } from "@/redux/slices/uiSlice";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import { useToast } from "@/hooks/useToast";
import { ROLE_LABELS } from "@/constants/roles";

export default function SettingsPage() {
  const user = useAppSelector((s) => s.auth.user);
  const darkMode = useAppSelector((s) => s.ui.darkMode);
  const dispatch = useAppDispatch();
  const { toast } = useToast();

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="font-display text-xl font-semibold text-slate-100">Settings</h1>
        <p className="text-sm text-muted mt-1">Manage your profile and workspace preferences.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
        </CardHeader>
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="h-16 w-16 rounded-full bg-gradient-to-br from-accent-purple to-accent-blue flex items-center justify-center text-xl font-semibold text-white">
              {user?.name?.charAt(0) ?? "A"}
            </div>
            <div>
              <p className="font-medium text-slate-100">{user?.name ?? "Analyst"}</p>
              <p className="text-sm text-muted">{user ? ROLE_LABELS[user.role] : "Security Analyst"}</p>
            </div>
          </div>
          <div>
            <label className="text-xs font-medium text-slate-400 mb-1.5 block">Full name</label>
            <Input defaultValue={user?.name} />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-400 mb-1.5 block">Email</label>
            <Input defaultValue={user?.email} type="email" />
          </div>
          <Button onClick={() => toast({ title: "Profile updated", variant: "success" })}>Save Changes</Button>
        </div>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Preferences</CardTitle>
        </CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-slate-200">Dark mode</p>
            <p className="text-xs text-muted">Toggle the dashboard color scheme</p>
          </div>
          <button
            onClick={() => dispatch(toggleDarkMode())}
            className={`relative h-6 w-11 rounded-full transition-colors ${darkMode ? "bg-accent-cyan" : "bg-slate-700"}`}
          >
            <span
              className={`absolute top-0.5 h-5 w-5 rounded-full bg-white transition-transform ${
                darkMode ? "translate-x-5" : "translate-x-0.5"
              }`}
            />
          </button>
        </div>
      </Card>
    </div>
  );
}