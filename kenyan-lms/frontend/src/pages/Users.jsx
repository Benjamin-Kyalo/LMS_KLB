import { useEffect, useMemo, useState } from "react";
import { useList } from "../hooks/useApi";
import { api, listAll } from "../services/api";
import { useToast } from "../context/ToastContext";
import { useAuth } from "../context/AuthContext";
import DataTable from "../components/DataTable";
import Modal from "../components/Modal";
import FormField from "../components/FormField";
import RollingLabel from "../components/RollingLabel";
import HoldToConfirmButton from "../components/HoldToConfirmButton";
import { TablePagination, TableToolbar } from "../components/TableTools";
import useTableControls from "../hooks/useTableControls";
import { canGrantRole, customRoleId, isSuperAdmin, roleLabel } from "../utilities/roles";

function optionKey(option) {
  if (!option) return "";
  return option.value === "CUSTOM" ? `CUSTOM:${customRoleId(option.custom_role)}` : option.value;
}

function userRoleKey(user) {
  if (!user) return "";
  return user.role === "CUSTOM" ? `CUSTOM:${customRoleId(user.custom_role)}` : user.role;
}

function roleName(user, options) {
  if (!user) return "—";
  if (user.role !== "CUSTOM") return roleLabel(user);
  if (user.custom_role_name) return user.custom_role_name;
  const match = options.find((option) => option.value === "CUSTOM"
    && customRoleId(option.custom_role) === customRoleId(user.custom_role));
  return match?.label || "Custom role";
}

export default function Users() {
  const { user: actor } = useAuth();
  const { data, loading, error, reload } = useList("/auth/users/");
  const { data: roleOptions, loading: rolesLoading } = useList("/auth/users/roles/");
  const { push } = useToast();
  const [institutions, setInstitutions] = useState([]);
  const [filter, setFilter] = useState("");
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({});
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState(null);
  const [resetResult, setResetResult] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);

  const roleChoices = useMemo(
    () => (roleOptions || []).filter((option) => canGrantRole(actor, option)),
    [roleOptions, actor],
  );

  useEffect(() => {
    if (!isSuperAdmin(actor)) return;
    let active = true;
    listAll("/institutions/")
      .then((rows) => { if (active) setInstitutions(rows); })
      .catch(() => { if (active) setInstitutions([]); });
    return () => { active = false; };
  }, [actor]);

  const rows = useMemo(
    () => (filter ? (data || []).filter((item) => userRoleKey(item) === filter) : (data || [])),
    [data, filter],
  );
  const controls = useTableControls(rows);

  function startCreate() {
    setEditing(null);
    const initial = roleChoices.find((option) => option.value === "LEARNER") || roleChoices[0];
    setForm({
      username: "", email: "", first_name: "", last_name: "", phone: "",
      role: initial?.value || "",
      custom_role: initial ? customRoleId(initial.custom_role) : null,
      institution: isSuperAdmin(actor) ? (actor.institution_id || "") : "",
      is_active: true,
    });
    setFormError(null);
    setOpen(true);
  }

  function startEdit(row) {
    setEditing(row);
    setForm({
      email: row.email || "", first_name: row.first_name || "", last_name: row.last_name || "",
      phone: row.phone || "", role: row.role, custom_role: customRoleId(row.custom_role),
      institution: row.institution || "",
      is_active: Boolean(row.is_active),
    });
    setFormError(null);
    setOpen(true);
  }

  function update(name, value) {
    setForm((previous) => ({ ...previous, [name]: value }));
  }

  function chooseRole(key) {
    const option = roleChoices.find((item) => optionKey(item) === key);
    setForm((previous) => ({
      ...previous,
      role: option?.value || "",
      custom_role: option ? customRoleId(option.custom_role) : null,
    }));
  }

  async function save(e) {
    e.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      const payload = { ...form };
      if (!isSuperAdmin(actor)) delete payload.institution;
      if (payload.role === "CUSTOM") payload.custom_role = customRoleId(payload.custom_role);
      else delete payload.custom_role;
      if (editing) {
        delete payload.username;
        await api.patch(`/auth/users/${editing.id}/`, payload);
      } else {
        await api.post("/auth/users/", payload);
      }
      push(`User ${editing ? "updated" : "created"}. No password was generated.`, "success");
      setOpen(false);
      setEditing(null);
      reload();
    } catch (err) {
      setFormError(err.message || "Something went wrong. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  async function toggleActive(row) {
    if (!row.is_active && row.role === "TEACHER" && !row.onboarding?.teacher_approved) {
      push("Approve this teacher in Teacher approvals before activating the account.", "error");
      return;
    }
    if (!row.is_active && !window.confirm(`Reactivate ${row.full_name || row.username}?`)) return;
    if (row.is_active && !window.confirm(`Deactivate ${row.full_name || row.username}?`)) return;
    try {
      await api.post(`/auth/users/${row.id}/set_active/`, { is_active: !row.is_active });
      push("Account status updated.", "success");
      reload();
    } catch (err) { push(err.message, "error"); }
  }

  async function resetPassword(row) {
    if (!window.confirm(`Reset the password for ${row.full_name || row.username}?`)) return;
    try {
      const result = await api.post(`/auth/users/${row.id}/reset_password/`, {});
      setResetResult({ username: row.username, password: result.temporary_password });
      push("Temporary password generated. Share it securely.", "success");
    } catch (err) { push(err.message, "error"); }
  }

  async function remove(row) {
    try {
      await api.del(`/auth/users/${row.id}/`);
      push("Account deleted.", "success");
      reload();
    } catch (err) { push(err.message, "error"); }
  }

  const selectedRoleKey = form.role === "CUSTOM" ? `CUSTOM:${form.custom_role || ""}` : (form.role || "");

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">Access control</div>
          <h1>User accounts</h1>
        </div>
        <div className="actions"><button onClick={startCreate}><RollingLabel>New user</RollingLabel></button></div>
      </div>

      <div className="notice info" style={{ marginBottom: "1rem" }}>
        Accounts are created without a password. Use the password reset flow after saving so
        the account owner sets their own credentials. Built-in administrator roles require an
        invitation; custom roles are assigned here and configured on the Roles screen.
        Publicly registered teachers and guardians remain restricted until reviewed in
        Teacher approvals and Guardian links.
      </div>

      <TableToolbar
        title="user accounts"
        controls={controls}
        onRefresh={reload}
        extra={(
          <label className="inline-filter">
            Role filter
            <select value={filter} onChange={(e) => setFilter(e.target.value)}>
              <option value="">All roles</option>
              {roleChoices.map((role) => (
                <option key={optionKey(role)} value={optionKey(role)}>{role.label}</option>
              ))}
            </select>
          </label>
        )}
      />

      <DataTable
        columns={[
          { key: "full_name", label: "Name", render: (r) => r.full_name || `${r.first_name || ""} ${r.last_name || ""}`.trim() || "—" },
          { key: "username", label: "Username" },
          { key: "admission_number", label: "Admission no.", render: (r) => r.admission_number ? <span className="mono">{r.admission_number}</span> : "—" },
          { key: "role", label: "Role", render: (r) => roleName(r, roleOptions || []) },
          { key: "institution_name", label: "Institution" },
          { key: "institution_code", label: "School code", render: (r) => r.institution_code || "—" },
          { key: "is_active", label: "Active", render: (r) => <span className={`tag ${r.is_active ? "good" : "bad"}`}>{r.is_active ? "Yes" : "No"}</span> },
          { key: "onboarding", label: "Setup", render: (r) => (
            <span className={`tag ${r.onboarding?.is_complete ? "good" : ""}`}>
              {r.onboarding?.is_complete ? "Complete" : "Pending"}
            </span>
          ) },
          { key: "_actions", label: "Actions", render: (r) => (
            <div className="row-actions">
              <button className="ghost small" aria-label={`Edit ${r.full_name || r.username || "record"}`} onClick={() => startEdit(r)}><RollingLabel>Edit</RollingLabel></button>
              {r.is_active ? (
                <HoldToConfirmButton
                  className="ghost small"
                  aria-label={`Deactivate ${r.full_name || r.username || "record"}`}
                  onConfirm={() => toggleActive(r)}
                >
                  Deactivate
                </HoldToConfirmButton>
              ) : (
                <button
                  className="ghost small"
                  aria-label={`Reactivate ${r.full_name || r.username || "record"}`}
                  onClick={() => toggleActive(r)}
                >
                  Reactivate
                </button>
              )}
              <button
                className="ghost small"
                aria-label={`Reset password for ${r.full_name || r.username || "record"}`}
                onClick={() => resetPassword(r)}
              >
                <RollingLabel>Reset password</RollingLabel>
              </button>
              <button
                className="ghost small danger"
                aria-label={`Delete ${r.full_name || r.username || "record"}`}
                onClick={() => setDeleteTarget(r)}
              >
                <RollingLabel>Delete</RollingLabel>
              </button>
            </div>
          ) },
        ]}
        rows={controls.visibleRows}
        loading={loading || rolesLoading}
        error={error}
        emptyTitle={controls.query || filter ? "No matching accounts" : "No user accounts yet"}
        emptyHint="Create an account or issue an administrator invitation."
      />

      {!loading && !rolesLoading && !error && <TablePagination controls={controls} />}

      {open && (
        <Modal title={`${editing ? "Edit" : "New"} user`} onClose={() => { setOpen(false); setEditing(null); }}>
          <form onSubmit={save}>
            {formError && <div className="notice error" role="alert" style={{ marginBottom: "0.75rem" }}>{formError}</div>}
            <fieldset className="form-section">
              <legend>Details</legend>
              <div className="form-grid">
                {!editing && <FormField label="Username" hint="Leave blank to generate from the name."><input value={form.username || ""} onChange={(e) => update("username", e.target.value)} /></FormField>}
                <FormField label="First name"><input value={form.first_name || ""} onChange={(e) => update("first_name", e.target.value)} required /></FormField>
                <FormField label="Last name"><input value={form.last_name || ""} onChange={(e) => update("last_name", e.target.value)} required /></FormField>
                <FormField label="Email" hint="Required for password reset"><input type="email" value={form.email || ""} onChange={(e) => update("email", e.target.value)} required /></FormField>
                <FormField label="Phone"><input value={form.phone || ""} onChange={(e) => update("phone", e.target.value)} /></FormField>
              </div>
            </fieldset>
            <fieldset className="form-section">
              <legend>Access &amp; setup</legend>
              <div className="form-grid">
                <FormField label="Role">
                  <select value={selectedRoleKey} onChange={(e) => chooseRole(e.target.value)} required>
                    <option value="">— choose —</option>
                    {roleChoices.map((role) => (
                      <option key={optionKey(role)} value={optionKey(role)}>{role.label}</option>
                    ))}
                  </select>
                </FormField>
                {isSuperAdmin(actor) && (
                  <FormField label="Institution">
                    <select value={form.institution || ""} onChange={(e) => update("institution", e.target.value)}>
                      <option value="">— none —</option>
                      {institutions.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                    </select>
                  </FormField>
                )}
                {editing && (
                  <FormField label="Active">
                    <input type="checkbox" style={{ width: "auto" }} checked={Boolean(form.is_active)} onChange={(e) => update("is_active", e.target.checked)} />
                  </FormField>
                )}
                <div className="full"><p className="muted">No password field: the API never generates or displays one. The account owner sets it through password reset.</p></div>
              </div>
            </fieldset>
            <div className="form-actions">
              <button type="button" className="ghost" onClick={() => { setOpen(false); setEditing(null); }}><RollingLabel>Cancel</RollingLabel></button>
              <button type="submit" disabled={saving}>{saving ? "Saving…" : <RollingLabel>Save user</RollingLabel>}</button>
            </div>
          </form>
        </Modal>
      )}
      {deleteTarget && (
        <Modal title="Delete account" onClose={() => setDeleteTarget(null)}>
          <p style={{ marginBottom: "1rem" }}>
            Delete the account for <strong>{deleteTarget.full_name || deleteTarget.username}</strong>? This cannot be undone.
          </p>
          <div className="form-actions">
            <button
              type="button"
              className="ghost"
              onClick={() => setDeleteTarget(null)}
            >
              <RollingLabel>Cancel</RollingLabel>
            </button>
            <button
              type="button"
              className="danger"
              onClick={async () => {
                const row = deleteTarget;
                setDeleteTarget(null);
                await remove(row);
              }}
            >
              <RollingLabel>Delete account</RollingLabel>
            </button>
          </div>
        </Modal>
      )}
      {resetResult && (
        <Modal title="Temporary password" onClose={() => setResetResult(null)}>
          <p className="muted" style={{ marginBottom: "0.75rem" }}>
            Share this temporary password with {resetResult.username} securely. They must change it on next sign-in.
          </p>
          <div className="notice info" style={{ marginBottom: "0.75rem" }}>
            <code>{resetResult.password}</code>
          </div>
          <div className="form-actions">
            <button
              type="button"
              onClick={async () => {
                try { await navigator.clipboard.writeText(resetResult.password); push("Temporary password copied.", "success"); }
                catch { push("Copy the password manually.", "info"); }
              }}
            >
              <RollingLabel>Copy password</RollingLabel>
            </button>
            <button type="button" className="ghost" onClick={() => setResetResult(null)}><RollingLabel>Close</RollingLabel></button>
          </div>
        </Modal>
      )}
    </section>
  );
}
