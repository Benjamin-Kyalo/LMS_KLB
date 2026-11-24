import { useEffect, useState } from "react";
import { useList } from "../hooks/useApi";
import { api, listAll } from "../services/api";
import { useToast } from "../context/ToastContext";
import { useAuth } from "../context/AuthContext";
import DataTable from "../components/DataTable";
import Modal from "../components/Modal";
import FormField from "../components/FormField";
import { TablePagination, TableToolbar } from "../components/TableTools";
import useTableControls from "../hooks/useTableControls";
import { formatDateTime } from "../utilities/format";
import { ADMIN_INVITATION_ROLES, ROLES, isPlatform } from "../utilities/roles";

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
  const [institutions, setInstitutions] = useState([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ email: "", role: "SCHOOL_ADMIN", institution: "" });
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState(null);
  const [newToken, setNewToken] = useState(null);

  useEffect(() => {
    if (!isPlatform(actor)) return;
    let active = true;
    listAll("/institutions/")
      .then((rows) => { if (active) setInstitutions(rows); })
      .catch(() => { if (active) setInstitutions([]); });
    return () => { active = false; };
  }, [actor]);

  function startCreate() {
    setForm({ email: "", role: "SCHOOL_ADMIN", institution: actor.institution_id || "" });
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
      if (isPlatform(actor)) payload.institution = form.institution;
      const result = await api.post("/auth/admin-invitations/", payload);
      setNewToken(result.token);
      push("Invitation created. Copy the token now.", "success");
      reload();
    } catch (err) {
      setFormError(err.details ? JSON.stringify(err.details) : err.message);
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
        <div className="actions"><button onClick={startCreate}>New invitation</button></div>
      </div>

      <div className="notice info" style={{ marginBottom: "1rem" }}>
        Invitations are single-use, expire after seven days and fix the administrator role
        and institution. Public registration cannot create administrator accounts.
      </div>

      <TableToolbar title="invitations" controls={controls} onRefresh={reload} />

      <DataTable
        columns={[
          { key: "email", label: "Email" },
          { key: "role", label: "Role", render: (r) => ROLES[r.role] || r.role },
          { key: "created_at", label: "Issued", render: (r) => formatDateTime(r.created_at) },
          { key: "expires_at", label: "Expires", render: (r) => formatDateTime(r.expires_at) },
          { key: "status", label: "Status", render: (r) => {
            const status = statusOf(r);
            const cls = status === "Usable" ? "good" : status === "Accepted" ? "bad" : "warn";
            return <span className={`tag ${cls}`}>{status}</span>;
          } },
          { key: "token", label: "Token", render: (r) => (
            <div className="row-actions">
              <button className="ghost small" onClick={() => copy(r.token)}>Copy</button>
            </div>
          ) },
          { key: "_actions", label: "Actions", render: (r) => (
            <button
              className="ghost small danger"
              disabled={r.revoked || Boolean(r.accepted_at)}
              onClick={() => revoke(r)}
            >
              Revoke
            </button>
          ) },
        ]}
        rows={controls.visibleRows}
        loading={loading}
        error={error}
        emptyTitle={controls.query ? "No matching invitations" : "No invitations yet"}
        emptyHint="Issue an invitation to create a school or institution administrator."
      />

      {!loading && !error && <TablePagination controls={controls} />}

      {open && (
        <Modal title="New administrator invitation" onClose={() => setOpen(false)}>
          <form onSubmit={save}>
            {formError && <div className="notice error" style={{ marginBottom: "0.75rem" }}>{formError}</div>}
            {newToken && (
              <div className="notice success invite-token" style={{ marginBottom: "0.75rem" }}>
                <strong>Copy this token now:</strong>
                <code>{newToken}</code>
                <button type="button" className="ghost small" onClick={() => copy(newToken)}>Copy</button>
              </div>
            )}
            <div className="form-grid">
              <FormField label="Invitee email" full><input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required /></FormField>
              <FormField label="Administrator role">
                <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} required>
                  {[...ADMIN_INVITATION_ROLES].map((role) => <option key={role} value={role}>{ROLES[role]}</option>)}
                </select>
              </FormField>
              {isPlatform(actor) && (
                <FormField label="Institution">
                  <select value={form.institution} onChange={(e) => setForm({ ...form, institution: e.target.value })} required>
                    <option value="">— choose —</option>
                    {institutions.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                  </select>
                </FormField>
              )}
            </div>
            <div className="form-actions">
              <button type="button" className="ghost" onClick={() => setOpen(false)}>Close</button>
              <button type="submit" disabled={saving}>{saving ? "Issuing…" : "Issue invitation"}</button>
            </div>
          </form>
        </Modal>
      )}
    </section>
  );
}
