import { useEffect, useMemo, useState } from "react";
import { useList } from "../hooks/useApi";
import { api, listAll } from "../services/api";
import { useToast } from "../context/ToastContext";
import { useAuth } from "../context/AuthContext";
import DataTable from "../components/DataTable";
import Modal from "../components/Modal";
import FormField from "../components/FormField";
import { TablePagination, TableToolbar } from "../components/TableTools";
import useTableControls from "../hooks/useTableControls";
import { PLATFORM_ROLES, ROLES, isPlatform } from "../utilities/roles";

function rolesForActor(actor) {
  if (!actor) return [];
  if (actor.role === "SUPER_ADMIN") return null; // all roles
  if (PLATFORM_ROLES.has(actor.role)) {
    return Object.keys(ROLES).filter((role) => role !== "SUPER_ADMIN");
  }
  // School and institution administrators may grant ordinary account roles
  // inside their own institution, never platform or super-admin roles.
  return Object.keys(ROLES).filter((role) => !PLATFORM_ROLES.has(role));
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

  const allowed = rolesForActor(actor);

  useEffect(() => {
    if (!isPlatform(actor)) return;
    let active = true;
    listAll("/institutions/")
      .then((rows) => { if (active) setInstitutions(rows); })
      .catch(() => { if (active) setInstitutions([]); });
    return () => { active = false; };
  }, [actor]);

  const rows = useMemo(
    () => (filter ? (data || []).filter((item) => item.role === filter) : (data || [])),
    [data, filter],
  );
  const controls = useTableControls(rows);

  function startCreate() {
    setEditing(null);
    setForm({
      username: "", email: "", first_name: "", last_name: "", phone: "",
      role: allowed && allowed.includes("LEARNER") ? "LEARNER" : (allowed ? allowed[0] : ""),
      institution: isPlatform(actor) ? (actor.institution_id || "") : "",
      is_active: true,
    });
    setFormError(null);
    setOpen(true);
  }

  function startEdit(row) {
    setEditing(row);
    setForm({
      email: row.email || "", first_name: row.first_name || "", last_name: row.last_name || "",
      phone: row.phone || "", role: row.role, institution: row.institution || "",
      is_active: Boolean(row.is_active),
    });
    setFormError(null);
    setOpen(true);
  }

  function update(name, value) {
    setForm((previous) => ({ ...previous, [name]: value }));
  }

  async function save(e) {
    e.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      const payload = { ...form };
      if (!isPlatform(actor)) delete payload.institution;
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
      setFormError(err.details ? JSON.stringify(err.details) : err.message);
    } finally {
      setSaving(false);
    }
  }

  async function toggleActive(row) {
    if (!row.is_active && !window.confirm(`Reactivate ${row.full_name || row.username}?`)) return;
    if (row.is_active && !window.confirm(`Deactivate ${row.full_name || row.username}?`)) return;
    try {
      await api.post(`/auth/users/${row.id}/set_active/`, { is_active: !row.is_active });
      push("Account status updated.", "success");
      reload();
    } catch (err) { push(err.message, "error"); }
  }

  async function remove(row) {
    if (!window.confirm(`Delete the account for ${row.full_name || row.username}?`)) return;
    try {
      await api.del(`/auth/users/${row.id}/`);
      push("Account deleted.", "success");
      reload();
    } catch (err) { push(err.message, "error"); }
  }

  const roleChoices = (roleOptions || []).filter(
    (option) => !allowed || allowed.includes(option.value),
  );

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">Access control</div>
          <h1>User accounts</h1>
        </div>
        <div className="actions"><button onClick={startCreate}>New user</button></div>
      </div>

      <div className="notice info" style={{ marginBottom: "1rem" }}>
        Accounts are created without a password. Use the password reset flow after saving so
        the account owner sets their own credentials. Privileged roles require an invitation.
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
              {roleChoices.map((role) => <option key={role.value} value={role.value}>{role.label}</option>)}
            </select>
          </label>
        )}
      />

      <DataTable
        columns={[
          { key: "full_name", label: "Name", render: (r) => r.full_name || `${r.first_name || ""} ${r.last_name || ""}`.trim() || "—" },
          { key: "username", label: "Username" },
          { key: "role", label: "Role", render: (r) => ROLES[r.role] || r.role },
          { key: "institution_name", label: "Institution" },
          { key: "is_active", label: "Active", render: (r) => <span className={`tag ${r.is_active ? "good" : "bad"}`}>{r.is_active ? "Yes" : "No"}</span> },
          { key: "_actions", label: "Actions", render: (r) => (
            <div className="row-actions">
              <button className="ghost small" onClick={() => startEdit(r)}>Edit</button>
              <button className="ghost small" onClick={() => toggleActive(r)}>{r.is_active ? "Deactivate" : "Reactivate"}</button>
              <button className="ghost small danger" onClick={() => remove(r)}>Delete</button>
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
            {formError && <div className="notice error" style={{ marginBottom: "0.75rem" }}>{formError}</div>}
            <div className="form-grid">
              {!editing && <FormField label="Username"><input value={form.username || ""} onChange={(e) => update("username", e.target.value)} required /></FormField>}
              <FormField label="First name"><input value={form.first_name || ""} onChange={(e) => update("first_name", e.target.value)} required /></FormField>
              <FormField label="Last name"><input value={form.last_name || ""} onChange={(e) => update("last_name", e.target.value)} required /></FormField>
              <FormField label="Email" hint="Required for password reset"><input type="email" value={form.email || ""} onChange={(e) => update("email", e.target.value)} required /></FormField>
              <FormField label="Phone"><input value={form.phone || ""} onChange={(e) => update("phone", e.target.value)} /></FormField>
              <FormField label="Role">
                <select value={form.role || ""} onChange={(e) => update("role", e.target.value)} required>
                  <option value="">— choose —</option>
                  {roleChoices.map((role) => <option key={role.value} value={role.value}>{role.label}</option>)}
                </select>
              </FormField>
              {isPlatform(actor) && (
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
              <div className="full"><p className="muted">No password field: the API never generates or displays one.</p></div>
            </div>
            <div className="form-actions">
              <button type="button" className="ghost" onClick={() => { setOpen(false); setEditing(null); }}>Cancel</button>
              <button type="submit" disabled={saving}>{saving ? "Saving…" : "Save user"}</button>
            </div>
          </form>
        </Modal>
      )}
    </section>
  );
}
