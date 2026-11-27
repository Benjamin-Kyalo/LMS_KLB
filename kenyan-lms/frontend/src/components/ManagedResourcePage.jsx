import ResourcePage from "./ResourcePage";
import { useAuth } from "../context/AuthContext";
import { useSiteContent } from "../context/SiteContentContext";
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

function emptyHintFor(endpoint, emptyStates) {
  const path = endpoint || "";
  let key;
  if (path === "/institutions/" || path === "/institutions/public-institutions/") key = "schools";
  else if (path.startsWith("/learners/")) key = "learners";
  else if (path.startsWith("/teachers/")) key = "teachers";
  else if (path.startsWith("/academics/classes/")) key = "classes";
  else if (path.startsWith("/courses/lessons/")) key = "lessons";
  else if (path.startsWith("/courses/assignments/")) key = "assignments";
  else if (path.startsWith("/assessments/")) key = "assessments";
  else if (path.startsWith("/content/")) key = "resources";
  else if (path.startsWith("/communications/notifications/")) key = "notifications";
  else if (path.startsWith("/communications/")) key = "messages";
  else if (path.startsWith("/reports/")) key = "reports";
  return key ? emptyStates?.[key]?.message : undefined;
}

// This is a thin permission wrapper around the generic CRUD component.
// It keeps every page's buttons aligned with what the backend will accept.
export default function ManagedResourcePage(props) {
  const { user } = useAuth();
  const { content } = useSiteContent();
  const allowedWrite = allowed(user, props.access || scopeFor(props.endpoint || ""));
  const emptyHint = props.emptyHint
    || emptyHintFor(props.endpoint, content.messages?.emptyStates);
  return (
    <ResourcePage
      {...props}
      emptyHint={emptyHint}
      canCreate={allowedWrite}
      canEdit={allowedWrite}
      canDelete={allowedWrite}
    />
  );
}
