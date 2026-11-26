import { useState } from "react";
import { useList } from "../hooks/useApi";
import { api } from "../services/api";
import { useToast } from "../context/ToastContext";
import { useAuth } from "../context/AuthContext";
import { isAdmin } from "../utilities/roles";
import DataTable from "../components/DataTable";
import Modal from "../components/Modal";
import FormField from "../components/FormField";
import RollingLabel from "../components/RollingLabel";
import { TablePagination, TableToolbar } from "../components/TableTools";
import useTableControls from "../hooks/useTableControls";

export default function Guardians() {
  const { user } = useAuth();
  const canWrite = isAdmin(user);
  const { data, loading, error, reload } = useList("/guardians/");
  const { data: learners } = useList("/learners/");
  const { push } = useToast();
  const controls = controls;
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({});
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [linkTarget, setLinkTarget] = useState(null);
  const [linkForm, setLinkForm] = useState({ learner: "", relationship: "Parent", is_primary: true });
  const [linkSaving, setLinkSaving] = useState(false);
  const [linkError, setLinkError] = useState(null);
  const [learnerSearch, setLearnerSearch] = useState("");

  function startCreate() {
    setEditing(null);
    setForm({ username: "", first_name: "", last_name: "", email: "", guardian_number: "", phone: "", occupation: "", relationship_to_learner: "", preferred_language: "en", receive_sms: true });
    setFormError(null);
    setOpen(true);
  }

  function startEdit(row) {
    setEditing(row);
    setForm({
      username: row.username || "",
      first_name: row.first_name || "",
      last_name: row.last_name || "",
      email: row.email || "",
      guardian_number: row.guardian_number || "",
      phone: row.phone || "",
      occupation: row.occupation || "",
      relationship_to_learner: row.relationship_to_learner || "",
      preferred_language: row.preferred_language || "en",
      receive_sms: row.receive_sms !== false,
    });
    setFormError(null);
    setOpen(true);
  }

  async function save(e) {
    e.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      if (editing) {
        await api.patch(`/guardians/${editing.id}/`, form);
        push("Guardian updated.", "success");
      } else {
        await api.post("/guardians/", form);
        push("Guardian created.", "success");
      }
      setOpen(false);
      setEditing(null);
      reload();
    } catch (err) {
      setFormError(err.message || "Could not save guardian.");
    } finally {
      setSaving(false);
    }
  }

  async function remove(row) {
    try {
      await api.del(`/guardians/${row.id}/`);
      push("Guardian deleted.", "success");
      reload();
    } catch (err) { push(err.message, "error"); }
  }

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">Parents & guardians</div>
          <h1>Guardians</h1>
        </div>
        <div className="actions">
          {canWrite && <button onClick={startCreate}><RollingLabel>New guardian</RollingLabel></button>}
        </div>
      </div>

      <TableToolbar title="guardians" controls={controls} onRefresh={reload} />

      <DataTable
        columns={[
          { key: "guardian_name", label: "Name" },
          { key: "guardian_number", label: "Guardian no.", render: (r) => <span className="mono">{r.guardian_number || "—"}</span> },
          { key: "institution_code", label: "School code", render: (r) => r.institution_code || "—" },
          { key: "learner_names", label: "Linked learners", render: (r) => (r.learner_names || []).join(", ") || "—" },
          { key: "email", label: "Email" },
          { key: "phone", label: "Phone" },
          { key: "relationship_to_learner", label: "Relationship" },
          { key: "_actions", label: "Actions", render: (r) => canWrite && (
            <div className="row-actions">
              {!(r.learner_names || []).length && (
                <button className="small" onClick={() => { setLinkTarget(r); setLinkForm({ learner: "", relationship: "Parent", is_primary: true }); setLearnerSearch(""); setLinkError(null); }}>
                  <RollingLabel>Link learner</RollingLabel>
                </button>
              )}
              <button className="ghost small" onClick={() => startEdit(r)}><RollingLabel>Edit</RollingLabel></button>
              <button className="ghost small danger" onClick={() => setDeleteTarget(r)}><RollingLabel>Delete</RollingLabel></button>
            </div>
          ) },
        ]}
        rows={controls.visibleRows}
        loading={loading}
        error={error}
        emptyTitle="No guardians yet"
        emptyHint="Create guardian accounts and link them to learners."
      />

      {!loading && !error && <TablePagination controls={controls} />}

      {open && (
        <Modal title={editing ? "Edit guardian" : "New guardian"} onClose={() => { setOpen(false); setEditing(null); }}>
          <form onSubmit={save}>
            {formError && <div className="notice error" role="alert" style={{ marginBottom: "0.75rem" }}>{formError}</div>}
            <div className="form-grid">
              {!editing && (
                <>
                  <FormField label="Username" hint="Leave blank to generate from the name."><input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} /></FormField>
                  <FormField label="First name"><input value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} required /></FormField>
                  <FormField label="Last name"><input value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} required /></FormField>
                </>
              )}
              {editing && (
                <>
                  <FormField label="Username"><input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} /></FormField>
                  <FormField label="First name"><input value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} required /></FormField>
                  <FormField label="Last name"><input value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} required /></FormField>
                </>
              )}
              <FormField label="Email"><input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></FormField>
              <FormField label="Guardian number" hint="Leave blank to generate GD-SCHOOL-001."><input value={form.guardian_number} onChange={(e) => setForm({ ...form, guardian_number: e.target.value })} /></FormField>
              <FormField label="Phone"><input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></FormField>
              <FormField label="Relationship"><input value={form.relationship_to_learner} onChange={(e) => setForm({ ...form, relationship_to_learner: e.target.value })} /></FormField>
              <FormField label="Occupation"><input value={form.occupation} onChange={(e) => setForm({ ...form, occupation: e.target.value })} /></FormField>
              <FormField label="Preferred language"><input value={form.preferred_language} onChange={(e) => setForm({ ...form, preferred_language: e.target.value })} /></FormField>
            </div>
            <div className="form-actions">
              <button type="button" className="ghost" onClick={() => { setOpen(false); setEditing(null); }}><RollingLabel>Cancel</RollingLabel></button>
              <button type="submit" disabled={saving}>{saving ? "Saving…" : <RollingLabel>{editing ? "Save changes" : "Create"}</RollingLabel>}</button>
            </div>
          </form>
        </Modal>
      )}

      {linkTarget && (
        <Modal title="Link learner to guardian" onClose={() => setLinkTarget(null)}>
          <form onSubmit={async (e) => {
            e.preventDefault();
            setLinkSaving(true);
            setLinkError(null);
            try {
              await api.post("/learners/guardian-links/", {
                learner: linkForm.learner,
                guardian: linkTarget.id,
                relationship: linkForm.relationship,
                is_primary: linkForm.is_primary,
              });
              push("Learner linked to guardian.", "success");
              setLinkTarget(null);
              reload();
            } catch (err) {
              setLinkError(err.message || "Could not link learner.");
            } finally {
              setLinkSaving(false);
            }
          }}>
            {linkError && <div className="notice error" role="alert" style={{ marginBottom: "0.75rem" }}>{linkError}</div>}
            <div className="form-grid">
              <FormField label="Search learner">
                <input value={learnerSearch} onChange={(e) => setLearnerSearch(e.target.value)} placeholder="Type name or admission number" />
              </FormField>
              <FormField label="Learner">
                <select value={linkForm.learner} onChange={(e) => setLinkForm({ ...linkForm, learner: e.target.value })} required>
                  <option value="">— choose learner —</option>
                  {(learners || [])
                    .filter((item) => {
                      const needle = learnerSearch.trim().toLowerCase();
                      if (!needle) return true;
                      return `${item.learner_name || ""} ${item.admission_number || ""} ${item.username || ""}`.toLowerCase().includes(needle);
                    })
                    .map((item) => <option key={item.id} value={item.id}>{item.learner_name || item.username} ({item.admission_number || "no number"})</option>)}
                </select>
              </FormField>
              <FormField label="Relationship"><input value={linkForm.relationship} onChange={(e) => setLinkForm({ ...linkForm, relationship: e.target.value })} required /></FormField>
              <FormField label="Primary link">
                <select value={linkForm.is_primary ? "yes" : "no"} onChange={(e) => setLinkForm({ ...linkForm, is_primary: e.target.value === "yes" })}>
                  <option value="yes">Yes</option>
                  <option value="no">No</option>
                </select>
              </FormField>
            </div>
            <div className="form-actions">
              <button type="button" className="ghost" onClick={() => setLinkTarget(null)}><RollingLabel>Cancel</RollingLabel></button>
              <button type="submit" disabled={linkSaving}>{linkSaving ? "Linking…" : <RollingLabel>Link learner</RollingLabel>}</button>
            </div>
          </form>
        </Modal>
      )}

      {deleteTarget && (
        <Modal title="Delete guardian" onClose={() => setDeleteTarget(null)}>
          <p style={{ marginBottom: "1rem" }}>
            Delete <strong>{deleteTarget.guardian_name || deleteTarget.username}</strong>? This cannot be undone.
          </p>
          <div className="form-actions">
            <button type="button" className="ghost" onClick={() => setDeleteTarget(null)}><RollingLabel>Cancel</RollingLabel></button>
            <button type="button" className="danger" onClick={async () => { const row = deleteTarget; setDeleteTarget(null); await remove(row); }}><RollingLabel>Delete</RollingLabel></button>
          </div>
        </Modal>
      )}
    </section>
  );
}