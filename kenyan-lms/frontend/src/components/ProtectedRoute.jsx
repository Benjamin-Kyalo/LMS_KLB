import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { isLoggedIn } from "../services/auth";
import { hasRole, homeFor } from "../utilities/roles";
import Loading from "./Loading";

export default function ProtectedRoute({ children, roles }) {
  const { user, refreshing } = useAuth();

  // A token alone is not proof of identity. Wait for /auth/me/ to finish
  // before deciding, otherwise a stale token causes a redirect loop.
  if (!isLoggedIn()) return <Navigate to="/login" replace />;
  if (refreshing) return <Loading />;
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !hasRole(user, roles)) return <Navigate to={homeFor(user)} replace />;
  return children;
}
