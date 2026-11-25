import { useMemo, useState } from "react";
import { useList } from "../hooks/useApi";
import { api } from "../services/api";
import { useToast } from "../context/ToastContext";
import DataTable from "../components/DataTable";
import Modal from "../components/Modal";
import FormField from "../components/FormField";
import RollingLabel from "../components/RollingLabel";
import HoldToConfirmButton from "../components/HoldToConfirmButton";
import {
  BUILT_IN_ROLES, CAPABILITIES, CAPABILITY_GROUPS, CAPABILITY_LABELS,
  customRoleId, roleLabel,
} from "../utilities/roles";

const emptyForm = () => ({ name: "", description: "", permissions: [], is_active: true });

function permissionsOf(role) {
  return Array.isArray(role?.permissions) ? role.permissions : [];
}

function countKey(row) {
  return row.role === "CUSTOM" ? `CUSTOM:${customRoleId(row.custom_role)}` : row.role;
}

export default function Roles() {
  const { data: customRoles, loading, error, reload } = useList("/auth/roles/");
  const { data: users, reload: reloadUsers } = useList("/auth/users/");
  const { push } = useToast();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState(null);

  const counts = useMemo(() => {
    const result = {};
    (users || []).forEach((user) => {
      const key = countKey(user);
      result[key] = (result[key] || 0) + 1;
    });
    return result;
  }, [users]);

  const rows = useMemo(() => {
    const builtIns = BUILT_IN_ROLES.map((role) => ({
      id: `builtin-${role.value}`,
      label: role.label,
      value: role.value,
      kind: "Built in",
      capabilitySummary: role.capabilitySummary,
      permissions: [],
      accounts: counts[role.value] || 0,
      custom: false,
    }));
    const custom = (customRoles || []).map((role) => {
      const permissions = permissionsOf(role);
      return {
        id: `custom-${role.id}`,
        label: role.name || roleLabel({ role: "CUSTOM", custom_role_name: role.name }),
        value: `custom_role:${role.id}`,
        kind: role.is_active === false ? "Custom · inactive" : "Custom",
        capabilitySummary: permissions.length
          ? permissions.map((capability) => CAPABILITY_LABELS[capability] || capability).join(", ")
          : "No capabilities selected",
        permissions,
        accounts: counts[`CUSTOM:${role.id}`] || 0,
        custom: true,
        record: role,
      };
    });
    return [...builtIns, ...custom];
  }, [customRoles, counts]);

  function startCreate() {
    setEditing(null);
    setForm(emptyForm());
    setFormError(null);
    setOpen(true);
  }

  function startEdit(row) {
    const role = row.record;
    setEditing(role);
    setForm({
      name: role.name || "",
      description: role.description || "",
      permissions: permissionsOf(role),
      is_active: role.is_active !== false,
    });
    setFormError(null);
    setOpen(true);
  }

  function close() {
    setOpen(false);
    setEditing(null);
    setFormError(null);
  }

  function togglePermission(capability) {
    setForm((previous) => ({
      ...previous,
      permissions: previous.permissions.includes(capability)
        ? previous.permissions.filter((item) => item !== capability)
        : [...previous.permissions, capability],
    }));
  }

  async function save(e) {
    e.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      const payload = {
        name: form.name.trim(),
        description: form.description.trim(),
        permissions: form.permissions,
        is_active: form.is_active,
      };
      if (editing) await api.patch(`/auth/roles/${editing.id}/`, payload);
      else await api.post("/auth/roles/", payload);
      push(`Custom role ${editing ? "updated" : "created"}.`, "success");
      close();
      reload();
      reloadUsers();
    } catch (err) {
      setFormError(err.details ? JSON.stringify(err.details) : err.message);
    } finally {
      setSaving(false);
    }
  }

  async function remove(row) {
    try {
      await api.del(`/auth/roles/${row.record.id}/`);
      push("Custom role deleted.", "success");
      reload();
      reloadUsers();
    } catch (err) { push(err.message, "error"); }
  }

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">Access control</div>
          <h1>Roles</h1>
        </div>
        <div className="actions">
          <button onClick={startCreate}><RollingLabel>New custom role</RollingLabel></button>
        </div>
      </div>

      <div className="notice info" style={{ marginBottom: "1rem" }}>
        Built-in roles are fixed by the application. Custom roles are reusable and stored by the
        API. Give a custom role <strong>{CAPABILITY_LABELS[CAPABILITIES.ADMIN_ACCESS]}</strong> if its
        users should see the admin portal; all other access is limited to the capabilities you
        select here.
      </div>

      <DataTable
        columns={[
          { key: "label", label: "Role" },
          { key: "kind", label: "Type", render: (r) => <span className="tag">{r.kind}</span> },
          { key: "value", label: "Code", render: (r) => <span className="mono">{r.value}</span> },
          { key: "capabilities", label: "Capabilities", render: (r) => (
            <span className={r.custom ? "muted" : undefined} style={{ fontSize: "0.82rem" }}>
              {r.capabilitySummary}
            </span>
          ) },
          { key: "accounts", label: "Accounts" },
          { key: "_actions", label: "Actions", render: (r) => (r.custom ? (
            <div className="row-actions">
              <button className="ghost small" aria-label={`Edit ${r.label}`} onClick={() => startEdit(r)}>
                <RollingLabel>Edit</RollingLabel>
              </button>
              <HoldToConfirmButton
                className="ghost small danger"
                aria-label={`Delete ${r.label}`}
                onConfirm={() => remove(r)}
              >
                Delete
              </HoldToConfirmButton>
            </div>
          ) : <span className="muted">Built in</span>) },
        ]}
        rows={rows}
        loading={loading}
        error={error}
        emptyTitle="No roles available"
        emptyHint="Built-in roles are always listed; create a custom role to add more."
      />

      {open && (
        <Modal title={`${editing ? "Edit" : "New"} custom role`} onClose={close}>
          <form onSubmit={save}>
            {formError && <div className="notice error" role="alert" style={{ marginBottom: "0.75rem" }}>{formError}</div>}
            <fieldset className="form-section">
              <legend>Details</legend>
              <div className="form-grid">
                <FormField label="Role name" hint="A short, reusable name shown in role pickers." full>
                  <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
                </FormField>
                <FormField label="Description" full>
                  <textarea
                    rows={2}
                    value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                  />
                </FormField>
                <FormField label="Active">
                  <input
                    type="checkbox"
                    style={{ width: "auto" }}
                    checked={form.is_active}
                    onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                  />
                </FormField>
              </div>
            </fieldset>

            <fieldset className="form-section">
              <legend>Capabilities</legend>
              <p className="muted" style={{ fontSize: "0.82rem", margin: "0 0 0.75rem" }}>
                {form.permissions.length
                  ? `${form.permissions.length} selected: ${form.permissions
                    .map((capability) => CAPABILITY_LABELS[capability] || capability).join(", ")}`
                  : "No capabilities selected yet."}
              </p>
              <div className="form-grid">
                {CAPABILITY_GROUPS.map((group) => (
                  <fieldset className="form-section" key={group.id}>
                    <legend>{group.label}</legend>
                    <div className="capability-picker" style={{ display: "grid", gap: "0.4rem" }}>
                      {group.capabilities.map((capability) => (
                        <label key={capability}>
                          <input
                            type="checkbox"
                            style={{ width: "auto", marginRight: "0.4rem" }}
                            checked={form.permissions.includes(capability)}
                            onChange={() => togglePermission(capability)}
                          />
                          {CAPABILITY_LABELS[capability]}
                        </label>
                      ))}
                    </div>
                  </fieldset>
                ))}
              </div>
            </fieldset>

            <div className="form-actions">
              <button type="button" className="ghost" onClick={close}><RollingLabel>Cancel</RollingLabel></button>
              <button type="submit" disabled={saving}>
                {saving ? "Saving…" : <RollingLabel>{editing ? "Save role" : "Create role"}</RollingLabel>}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </section>
  );
}
