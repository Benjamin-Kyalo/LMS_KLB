import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { canUseAdmin, hasCapability, hasRole, homeFor, isCustomRole } from "../utilities/roles";
import Loading from "./Loading";

// A route may be restricted by role, by capability, or by either one. The
// capability path lets a CUSTOM user reach pages enabled for their role while
// built-in users keep the existing role-based behaviour.
export default function ProtectedRoute({ children, roles, capability }) {
  const { user, refreshing } = useAuth();
  const location = useLocation();

  // Identity comes only from the server session. Wait for /auth/me/ so a stale
  // cached role can never unlock a protected route.
  if (refreshing) return <Loading />;
  if (!user) return <Navigate to="/login" replace />;

  const roleAllowed = Boolean(roles && hasRole(user, roles));
  const capabilityAllowed = Boolean(capability && hasCapability(user, capability));
  // A capability alone never unlocks the admin portal for a custom role whose
  // own permissions did not include admin.access.
  const customWithoutAdminAccess = isCustomRole(user) && !canUseAdmin(user);
  if ((roles || capability) && (customWithoutAdminAccess || (!roleAllowed && !capabilityAllowed))) {
    // An admin denied a page inside /admin would otherwise bounce to /admin
    // again, so fall back to the public home in that case.
    const home = homeFor(user);
    return <Navigate to={home && home !== location.pathname ? home : "/"} replace />;
  }
  return children;
}
