import { useEffect, useMemo, useState } from "react";
import { Copy, KeyRound, ShieldCheck, TriangleAlert, UserRound } from "lucide-react";
import { useList } from "../hooks/useApi";
import { api, listAll } from "../services/api";
import { useToast } from "../context/ToastContext";
import { useAuth } from "../context/AuthContext";
import DataTable from "../components/DataTable";
import Modal from "../components/Modal";
import FormField from "../components/FormField";
import RollingLabel from "../components/RollingLabel";
import { DialogLead, DialogSection } from "../components/DialogParts";
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

function personName(row) {
  if (!row) return "this account";
  if (row.full_name) return row.full_name;
  const joined = [row.first_name, row.last_name].filter(Boolean).join(" ").trim();
  return joined || row.username || "this account";
}

function initials(name) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase() || "?";
}

function AccountSummary({ row, role }) {
  const name = personName(row);
  return (
    <div className="account-summary">
      <div className="account-avatar" aria-hidden="true">{initials(name)}</div>
      <div className="account-summary-copy">
        <strong>{name}</strong>
        <span>@{row.username || "no username"} · {role}</span>
      </div>
      <span className={`tag ${row.is_active ? "good" : "bad"}`}>
        {row.is_active ? "Active" : "Inactive"}
      </span>
    </div>
  );
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
  const [resetTarget, setResetTarget] = useState(null);
  const [resetBusy, setResetBusy] = useState(false);
  const [resetError, setResetError] = useState(null);
  const [resetResult, setResetResult] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleteBusy, setDeleteBusy] = useState(false);
  const [deleteError, setDeleteError] = useState(null);
  const [statusTarget, setStatusTarget] = useState(null);
  const [statusBusy, setStatusBusy] = useState(false);
  const [statusError, setStatusError] = useState(null);

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

  function requestStatus(row) {
    setStatusTarget(row);
    setStatusError(null);
  }

  async function applyStatus() {
    const row = statusTarget;
    const nextActive = !row.is_active;
    if (nextActive && row.role === "TEACHER" && !row.onboarding?.teacher_approved) {
      push("Approve this teacher in Teacher approvals before activating the account.", "error");
      return;
    }
    setStatusBusy(true);
    setStatusError(null);
    try {
      await api.post(`/auth/users/${row.id}/set_active/`, { is_active: nextActive });
      push("Account status updated.", "success");
      setStatusTarget(null);
      reload();
    } catch (err) {
      setStatusError(err.message || "The account status could not be changed.");
    } finally {
      setStatusBusy(false);
    }
  }

  function requestReset(row) {
    setResetTarget(row);
    setResetError(null);
  }

  async function confirmReset() {
    const row = resetTarget;
    setResetBusy(true);
    setResetError(null);
    try {
      const result = await api.post(`/auth/users/${row.id}/reset_password/`, {});
      setResetResult({
        username: row.username,
        fullName: personName(row),
        role: roleName(row, roleOptions || []),
        password: result.temporary_password,
      });
      setResetTarget(null);
      push("Temporary password generated. Share it securely.", "success");
    } catch (err) {
      setResetError(err.message || "The password could not be reset.");
    } finally {
      setResetBusy(false);
    }
  }

  async function copyPassword() {
    try {
      await navigator.clipboard.writeText(resetResult.password);
      push("Temporary password copied.", "success");
    } catch {
      push("Copy the password manually.", "info");
    }
  }

  async function remove(row) {
    setDeleteBusy(true);
    setDeleteError(null);
    try {
      await api.del(`/auth/users/${row.id}/`);
      setDeleteTarget(null);
      push("Account deleted.", "success");
      reload();
    } catch (err) {
      setDeleteError(err.message || "The account could not be deleted.");
    } finally {
      setDeleteBusy(false);
    }
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

      <div className="notice info dialog-error" role="note">
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
                <button
                  className="ghost small"
                  aria-label={`Deactivate ${r.full_name || r.username || "record"}`}
                  onClick={() => requestStatus(r)}
                >
                  <RollingLabel>Deactivate</RollingLabel>
                </button>
              ) : (
                <button
                  className="ghost small"
                  aria-label={`Reactivate ${r.full_name || r.username || "record"}`}
                  onClick={() => requestStatus(r)}
                >
                  <RollingLabel>Reactivate</RollingLabel>
                </button>
              )}
              <button
                className="ghost small"
                aria-label={`Reset password for ${r.full_name || r.username || "record"}`}
                onClick={() => requestReset(r)}
              >
                <RollingLabel>Reset password</RollingLabel>
              </button>
              <button
                className="ghost small danger"
                aria-label={`Delete ${r.full_name || r.username || "record"}`}
                onClick={() => { setDeleteTarget(r); setDeleteError(null); }}
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
        <Modal
          title={`${editing ? "Edit" : "New"} user`}
          onClose={() => { setOpen(false); setEditing(null); }}
        >
          <form onSubmit={save}>
            <DialogLead icon={UserRound} kicker="User management">
              {editing
                ? "Update the person's details and access. Nothing here creates or displays a password."
                : "Create the account first, then use Reset password so the owner sets their own credentials."}
            </DialogLead>
            {formError && <div className="notice error dialog-error" role="alert">{formError}</div>}
            <DialogSection title="Personal details" hint="Used for identification and account recovery.">
              <div className="form-grid">
                {!editing && <FormField label="Username" hint="Leave blank to generate from the name."><input value={form.username || ""} onChange={(e) => update("username", e.target.value)} /></FormField>}
                <FormField label="First name"><input value={form.first_name || ""} onChange={(e) => update("first_name", e.target.value)} required /></FormField>
                <FormField label="Last name"><input value={form.last_name || ""} onChange={(e) => update("last_name", e.target.value)} required /></FormField>
                <FormField label="Email" hint="Required for password reset"><input type="email" value={form.email || ""} onChange={(e) => update("email", e.target.value)} required /></FormField>
                <FormField label="Phone"><input value={form.phone || ""} onChange={(e) => update("phone", e.target.value)} /></FormField>
              </div>
            </DialogSection>
            <DialogSection title="Access and setup" hint="Roles are enforced by the API, not only by this form.">
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
            </DialogSection>
            <div className="dialog-actions">
              <button type="button" className="ghost" onClick={() => { setOpen(false); setEditing(null); }}><RollingLabel>Cancel</RollingLabel></button>
              <button type="submit" disabled={saving} aria-busy={saving || undefined}>
                {saving ? "Saving…" : <RollingLabel>Save user</RollingLabel>}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {statusTarget && (
        <Modal
          title={statusTarget.is_active ? "Deactivate account" : "Reactivate account"}
          onClose={() => setStatusTarget(null)}
        >
          <DialogLead
            icon={statusTarget.is_active ? TriangleAlert : UserRound}
            tone={statusTarget.is_active ? "warn" : "info"}
            kicker="Account status"
          >
            {statusTarget.is_active
              ? "The person will be signed out and unable to sign in until the account is reactivated."
              : "The person will be able to sign in again immediately with their existing credentials."}
          </DialogLead>
          <AccountSummary row={statusTarget} role={roleName(statusTarget, roleOptions || [])} />
          <div className={`notice ${statusTarget.is_active ? "warning" : "info"}`} role="note">
            {statusTarget.is_active
              ? "Their records and history stay in place. Only access is paused."
              : "Check that the account is approved and its details are current before restoring access."}
          </div>
          {statusError && <div className="notice error dialog-error" role="alert">{statusError}</div>}
          <DialogSection title="Confirm change">
            <ol className="dialog-steps">
              <li>{statusTarget.is_active ? "Existing sessions are ended." : "No password is changed."}</li>
              <li>The change is recorded in the audit trail.</li>
            </ol>
          </DialogSection>
          <div className="dialog-actions">
            <button type="button" className="ghost" onClick={() => setStatusTarget(null)}><RollingLabel>Cancel</RollingLabel></button>
            {statusTarget.is_active ? (
              <button
                type="button"
                className="danger"
                disabled={statusBusy}
                aria-busy={statusBusy || undefined}
                onClick={applyStatus}
              >
                {statusBusy ? "Deactivating…" : "Deactivate account"}
              </button>
            ) : (
              <button type="button" disabled={statusBusy} aria-busy={statusBusy || undefined} onClick={applyStatus}>
                {statusBusy ? "Reactivating…" : <RollingLabel>Reactivate account</RollingLabel>}
              </button>
            )}
          </div>
        </Modal>
      )}

      {resetTarget && (
        <Modal
          title={`Reset password for ${personName(resetTarget)}`}
          onClose={() => setResetTarget(null)}
        >
          <DialogLead icon={KeyRound} tone="warn" kicker="Account security">
            This issues a one-time temporary password and signs the person out of every device.
          </DialogLead>
          <AccountSummary row={resetTarget} role={roleName(resetTarget, roleOptions || [])} />
          <div className="notice warning" role="note">
            Share the temporary password through a private channel only. It is shown once and the
            person must choose a new password at their next sign-in.
          </div>
          {resetError && <div className="notice error dialog-error" role="alert">{resetError}</div>}
          <DialogSection title="What happens next">
            <ol className="dialog-steps">
              <li>All current sessions for this account are ended.</li>
              <li>A temporary password is generated and shown once in the next window.</li>
              <li>The account owner replaces it at the next sign-in.</li>
            </ol>
          </DialogSection>
          <div className="dialog-actions">
            <button type="button" className="ghost" onClick={() => setResetTarget(null)}><RollingLabel>Cancel</RollingLabel></button>
            <button
              type="button"
              disabled={resetBusy}
              aria-busy={resetBusy || undefined}
              onClick={confirmReset}
            >
              {resetBusy ? "Generating…" : "Generate temporary password"}
            </button>
          </div>
        </Modal>
      )}

      {deleteTarget && (
        <Modal title="Delete account" onClose={() => setDeleteTarget(null)}>
          <DialogLead icon={TriangleAlert} tone="bad" kicker="Permanent action">
            This removes the login account. It cannot be undone from this screen.
          </DialogLead>
          <AccountSummary row={deleteTarget} role={roleName(deleteTarget, roleOptions || [])} />
          <div className="notice error" role="note">
            Delete is reserved for duplicate or mistaken accounts. Use Deactivate instead when a
            person is simply leaving temporarily; that keeps their school history intact.
          </div>
          {deleteError && <div className="notice error dialog-error" role="alert">{deleteError}</div>}
          <DialogSection title="Before you continue">
            <ol className="dialog-steps">
              <li>Confirm the name and username above match the intended person.</li>
              <li>Check that no records still need to be reassigned to another account.</li>
            </ol>
          </DialogSection>
          <div className="dialog-actions">
            <button type="button" className="ghost" onClick={() => setDeleteTarget(null)}><RollingLabel>Cancel</RollingLabel></button>
            <button
              type="button"
              className="danger"
              disabled={deleteBusy}
              aria-busy={deleteBusy || undefined}
              onClick={() => remove(deleteTarget)}
            >
              {deleteBusy ? "Deleting…" : "Delete account"}
            </button>
          </div>
        </Modal>
      )}

      {resetResult && (
        <Modal title="Temporary password ready" onClose={() => setResetResult(null)}>
          <DialogLead icon={ShieldCheck} tone="good" kicker="One-time credential">
            The password below is shown only in this window. Copy it now and share it privately.
          </DialogLead>
          <div className="account-summary">
            <div className="account-avatar" aria-hidden="true">{initials(resetResult.fullName)}</div>
            <div className="account-summary-copy">
              <strong>{resetResult.fullName}</strong>
              <span>@{resetResult.username || "no username"} · {resetResult.role}</span>
            </div>
          </div>
          <DialogSection title="Temporary password" hint="They must change it at the next sign-in.">
            <div className="credential-box">
              <code>{resetResult.password}</code>
              <button type="button" className="secondary small" onClick={copyPassword}>
                <Copy size={14} aria-hidden="true" /> Copy
              </button>
            </div>
          </DialogSection>
          <DialogSection title="Share it safely">
            <ol className="dialog-steps">
              <li>Send it through a private channel, not a group chat or open document.</li>
              <li>Ask the person to sign in and replace it immediately.</li>
              <li>Close this window when you have saved it; it will not be shown again.</li>
            </ol>
          </DialogSection>
          <div className="dialog-actions">
            <button type="button" className="ghost" onClick={() => setResetResult(null)}><RollingLabel>Close</RollingLabel></button>
            <button type="button" onClick={copyPassword}><RollingLabel>Copy password</RollingLabel></button>
          </div>
        </Modal>
      )}
    </section>
  );
}
