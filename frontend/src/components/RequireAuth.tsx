import { Navigate, useLocation } from "react-router";
import { useMe } from "../api/queries/auth";
import { CenterSpinner } from "./ui/Spinner";

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const me = useMe();
  const location = useLocation();
  if (me.isLoading) return <CenterSpinner />;
  if (!me.data) {
    const next = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/login?next=${next}`} replace />;
  }
  return <>{children}</>;
}
