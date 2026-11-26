import { useEffect, useRef, useState } from "react";
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
import { formatDateTime } from "../utilities/format";
import { ADMIN_INVITATION_ROLES, isSuperAdmin, roleLabel } from "../utilities/roles";

function statusOf(row) {
  if (row.revoked) return "Revoked";
  if (row.accepted_at) return "Accepted";
  if (new Date(row.expires_at) < new Date()) return "Expired";
  return "Usable";
}

export default function AdminInvitations() {
  const { user: actor } = useAuth();
  const { data, loading, error, reload } = useList("/auth/admin-invitations/");
  const { push } = useToast();
  const controls = useTableControls(data);
  const canGrantSuper = isSuperAdmin(actor);
  const invitationRoles = canGrantSuper
    ? ["SUPER_ADMIN", ...ADMIN_INVITATION_ROLES]
    : [...ADMIN_INVITATION_ROLES];
  const [institutions, setInstitutions] = useState([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ email: "", role: "ADMIN", institution: "" });
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState(null);
  const [newToken, setNewToken] = useState(null);
  const [copiedToken, setCopiedToken] = useState(null);
  const copyTimer = useRef(null);

  useEffect(() => () => {
    if (copyTimer.current !== null) clearTimeout(copyTimer.current);
  }, []);

  useEffect(() => {
    if (!isSuperAdmin(actor)) return;
    let active = true;
    listAll("/institutions/")
      .then((rows) => { if (active) setInstitutions(rows); })
      .catch(() => { if (active) setInstitutions([]); });
    return () => { active = false; };
  }, [actor]);

  function startCreate() {
    setForm({ email: "", role: "ADMIN", institution: actor.institution_id || "" });
    setFormError(null);
    setNewToken(null);
    setOpen(true);
  }

  async function save(e) {
    e.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      const payload = { email: form.email, role: form.role };
      if (isSuperAdmin(actor)) payload.institution = form.institution;
      const result = await api.post("/auth/admin-invitations/", payload);
      setNewToken(result.token);
      push("Invitation created. Copy the token now.", "success");
      reload();
    } catch (err) {
      setFormError(err.message || "Something went wrong. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  async function revoke(row) {
    if (!window.confirm(`Revoke the invitation for ${row.email}?`)) return;
    try {
      await api.del(`/auth/admin-invitations/${row.id}/`);
      push("Invitation revoked.", "success");
      reload();
    } catch (err) { push(err.message, "error"); }
  }

  async function copy(token) {
    try {
      await navigator.clipboard.writeText(token);
      push("Token copied to clipboard.", "success");
      setCopiedToken(token);
      if (copyTimer.current !== null) clearTimeout(copyTimer.current);
      copyTimer.current = setTimeout(() => setCopiedToken(null), 1500);
    } catch {
      push("Select the token and copy it manually.", "info");
    }
  }

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">Access control</div>
          <h1>Administrator invitations</h1>
        </div>
        <div className="actions"><button onClick={startCreate}><RollingLabel>New invitation</RollingLabel></button></div>
      </div>

      <div className="notice info" style={{ marginBottom: "1rem" }}>
        Invitations are single-use, expire after seven days and fix the built-in administrator
        role and institution. Custom roles are assigned on the Users screen. Public registration
        cannot create administrator accounts.
      </div>

      <TableToolbar title="invitations" controls={controls} onRefresh={reload} />

      <DataTable
        columns={[
          { key: "email", label: "Email" },
          { key: "role", label: "Role", render: (r) => roleLabel(r) },
          { key: "created_at", label: "Issued", render: (r) => formatDateTime(r.created_at) },
          { key: "expires_at", label: "Expires", render: (r) => formatDateTime(r.expires_at) },
          { key: "status", label: "Status", render: (r) => {
            const status = statusOf(r);
            const cls = status === "Usable" ? "good" : status === "Accepted" ? "bad" : "warn";
            return <span className={`tag ${cls}`}>{status}</span>;
          } },
          { key: "token", label: "Token", render: (r) => (
            <div className="row-actions">
              <button
                className="ghost small"
                aria-label={`${copiedToken === r.token ? "Copied" : "Copy"} invitation token for ${r.email || "record"}`}
                onClick={() => copy(r.token)}
              >
                {copiedToken === r.token ? "Copied" : "Copy"}
              </button>
            </div>
          ) },
          { key: "_actions", label: "Actions", render: (r) => (
            <HoldToConfirmButton
              className="ghost small danger"
              disabled={r.revoked || Boolean(r.accepted_at)}
              aria-label={`Revoke invitation for ${r.email || "record"}`}
              onConfirm={() => revoke(r)}
            >
              Revoke
            </HoldToConfirmButton>
          ) },
        ]}
        rows={controls.visibleRows}
        loading={loading}
        error={error}
        emptyTitle={controls.query ? "No matching invitations" : "No invitations yet"}
        emptyHint="Issue an invitation to create an administrator account."
      />

      {!loading && !error && <TablePagination controls={controls} />}

      {open && (
        <Modal title="New administrator invitation" onClose={() => setOpen(false)}>
          <form onSubmit={save}>
            {formError && <div className="notice error" role="alert" style={{ marginBottom: "0.75rem" }}>{formError}</div>}
            {newToken && (
              <div className="notice success invite-token" role="status" style={{ marginBottom: "0.75rem" }}>
                <strong>Copy this token now:</strong>
                <code>{newToken}</code>
                <button
                  type="button"
                  className="ghost small"
                  aria-label={copiedToken === newToken ? "Copied invitation token" : "Copy invitation token"}
                  onClick={() => copy(newToken)}
                >
                  {copiedToken === newToken ? "Copied" : "Copy"}
                </button>
              </div>
            )}
            <div className="form-grid">
              <FormField label="Invitee email" full><input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required /></FormField>
              <FormField label="Administrator role">
                <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} required>
                  {invitationRoles.map((role) => (
                    <option key={role} value={role}>{roleLabel({ role })}</option>
                  ))}
                </select>
              </FormField>
              {canGrantSuper && (
                <FormField label="Institution">
                  <select value={form.institution} onChange={(e) => setForm({ ...form, institution: e.target.value })} required>
                    <option value="">— choose —</option>
                    {institutions.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                  </select>
                </FormField>
              )}
            </div>
            <div className="form-actions">
              <button type="button" className="ghost" onClick={() => setOpen(false)}><RollingLabel>Close</RollingLabel></button>
              <button type="submit" disabled={saving}>{saving ? "Issuing…" : <RollingLabel>Issue invitation</RollingLabel>}</button>
            </div>
          </form>
        </Modal>
      )}
    </section>
  );
}
