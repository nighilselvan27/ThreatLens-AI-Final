import { Navigate } from "react-router-dom";
import { useAppSelector } from "@/redux/hooks";
import { canAccess, PageKey } from "@/constants/roles";

export default function RequireRole({
  page,
  children,
}: {
  page: PageKey;
  children: JSX.Element;
}) {
  const user = useAppSelector((s) => s.auth.user);

  if (!canAccess(user?.role, page)) {
    return <Navigate to="/access-denied" replace />;
  }

  return children;
}