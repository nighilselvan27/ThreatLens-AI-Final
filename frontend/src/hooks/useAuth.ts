import { useAppSelector } from "@/redux/hooks";

export function useAuth() {
  const { user, isAuthenticated, status, error } = useAppSelector((s) => s.auth);
  return { user, isAuthenticated, status, error };
}
