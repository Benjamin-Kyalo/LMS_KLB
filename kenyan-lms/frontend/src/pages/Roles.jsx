import { useMemo } from "react";
import { useList } from "../hooks/useApi";
import DataTable from "../components/DataTable";
import {
  ADMIN_INVITATION_ROLES, PLATFORM_ROLES, PUBLIC_REGISTRATION_ROLES,
  ROLES, SCHOOL_ADMIN_ROLES,
} from "../utilities/roles";

const ASSIGNERS = {
  SUPER_ADMIN: "Super administrator only",
  PLATFORM_ADMIN: "Platform administrators",
  INSTITUTION_ADMIN: "Platform and institution administrators",
  SCHOOL_ADMIN: "Administrators; school admins only in their own school",
  TEACHER: "Administrators, or pending self-request approved by a school",
  LEARNER: "Administrators, or public registration with role-specific fields",
  GUARDIAN: "Administrators, or public registration with relationship details",
  CONTENT_MANAGER: "Platform administrators",
};

function assignmentRoute(role) {
  if (PLATFORM_ROLES.has(role)) return "Platform role — invitation/account assignment";
  if (ADMIN_INVITATION_ROLES.has(role)) return "Admin invitation or Users screen";
  if (PUBLIC_REGISTRATION_ROLES.has(role)) return "Public registration or Users screen";
  return "Users screen only";
}

export default function Roles() {
  const { data: roles, loading, error } = useList("/auth/users/roles/");
  const { data: users } = useList("/auth/users/");

  const counts = useMemo(() => {
    const result = {};
    (users || []).forEach((user) => { result[user.role] = (result[user.role] || 0) + 1; });
    return result;
  }, [users]);

  const rows = (roles || []).map((role) => ({
    id: role.value,
    value: role.value,
    label: ROLES[role.value] || role.label,
    assigner: ASSIGNERS[role.value] || "Administrator",
    route: assignmentRoute(role.value),
    count: counts[role.value] || 0,
    privileged: PLATFORM_ROLES.has(role.value) || SCHOOL_ADMIN_ROLES.has(role.value) ? "Yes" : "No",
  }));

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">Access control</div>
          <h1>Roles</h1>
        </div>
      </div>
      <div className="notice info" style={{ marginBottom: "1rem" }}>
        Roles are enforced by the API, not only by these screens. Role definitions are
        application constants; change a person&apos;s role on the <strong>Users</strong> screen,
        and issue privileged roles only through an administrator invitation.
      </div>
      <DataTable
        columns={[
          { key: "label", label: "Role" },
          { key: "value", label: "Code", render: (r) => <span className="mono">{r.value}</span> },
          { key: "assigner", label: "Who may assign" },
          { key: "route", label: "Creation route" },
          { key: "privileged", label: "Privileged" },
          { key: "count", label: "Accounts" },
        ]}
        rows={rows}
        loading={loading}
        error={error}
        emptyTitle="No roles available"
        emptyHint="Roles come from the backend role list."
      />
    </section>
  );
}
