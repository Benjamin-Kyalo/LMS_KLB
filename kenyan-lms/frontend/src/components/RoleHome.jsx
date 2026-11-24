import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { homeFor } from "../utilities/roles";

// Sends each role to the correct "side" of the application.
// Old page addresses use this component so bookmarks keep working.
export default function RoleHome({ adminTo = "/admin", portalTo = "/portal" }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (portalTo === "/portal" && adminTo === "/admin") {
    return <Navigate to={homeFor(user)} replace />;
  }
  return <Navigate to={homeFor(user).startsWith("/portal") ? portalTo : adminTo} replace />;
}
