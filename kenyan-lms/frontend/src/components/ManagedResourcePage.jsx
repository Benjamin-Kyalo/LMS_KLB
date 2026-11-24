import ResourcePage from "./ResourcePage";
import { useAuth } from "../context/AuthContext";
import { canWriteContent, canWriteTeaching, isAdmin, isPlatform } from "../utilities/roles";

// Reads are available to everyone who can open the page. Writes follow the
// same authority rules as the API's AdminWriteMixin / StaffWriteMixin /
// ContentWriteMixin. Unknown endpoints fail closed (read only).
function scopeFor(endpoint) {
  if (endpoint === "/institutions/" || endpoint.startsWith("/curriculum/")) return "platform";
  if (
    endpoint.startsWith("/institutions/") ||
    ["/teachers/", "/guardians/", "/learners/", "/academics/events/"].includes(endpoint)
  ) return "admin";
  if (endpoint.startsWith("/content/")) return "content";
  if (endpoint === "/courses/submissions/") return "readOnly";
  if (
    endpoint.startsWith("/courses/") ||
    endpoint.startsWith("/assessments/") ||
    endpoint.startsWith("/attendance/") ||
    endpoint.startsWith("/academics/") ||
    endpoint.startsWith("/communications/")
  ) return "staff";
  return "readOnly";
}

function allowed(user, scope) {
  switch (scope) {
    case "platform": return isPlatform(user);
    case "admin": return isAdmin(user);
    case "staff": return canWriteTeaching(user);
    case "content": return canWriteContent(user);
    default: return false;
  }
}

// This is a thin permission wrapper around the generic CRUD component.
// It keeps every page's buttons aligned with what the backend will accept.
export default function ManagedResourcePage(props) {
  const { user } = useAuth();
  const allowedWrite = allowed(user, props.access || scopeFor(props.endpoint || ""));
  return (
    <ResourcePage
      {...props}
      canCreate={allowedWrite}
      canEdit={allowedWrite}
      canDelete={allowedWrite}
    />
  );
}
