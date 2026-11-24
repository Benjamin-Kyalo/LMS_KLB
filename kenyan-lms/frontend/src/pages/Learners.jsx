import { useState } from "react";
import { useList } from "../hooks/useApi";
import { api } from "../services/api";
import { useToast } from "../context/ToastContext";
import { useAuth } from "../context/AuthContext";
import { isAdmin } from "../utilities/roles";
import DataTable from "../components/DataTable";
import Modal from "../components/Modal";
import FormField from "../components/FormField";
import { TablePagination, TableToolbar } from "../components/TableTools";
import useTableControls from "../hooks/useTableControls";
import { statusTag } from "../utilities/format";

export default function Learners() {
  const { user } = useAuth();
  const canWrite = isAdmin(user);
  const { data, loading, error, reload } = useList("/learners/");
  const { push } = useToast();
  const controls = useTableControls(data);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({});
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState(null);

  function startCreate() {
    setForm({ username: "", first_name: "", last_name: "", admission_number: "" });
    setFormError(null);
    setOpen(true);
  }

  async function save(e) {
    e.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      const result = await api.post("/learners/", form);
      push(result?.queued ? "Learner saved offline; it will sync when you reconnect." : "Learner registered.", "success");
      setOpen(false);
      reload();
    } catch (err) {
      setFormError(err.details ? JSON.stringify(err.details) : err.message);
    } finally { setSaving(false); }
  }

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">Student information</div>
          <h1>Learners</h1>
        </div>
        <div className="actions">
          {canWrite && <button onClick={startCreate}>Register learner</button>}
        </div>
      </div>

      <TableToolbar title="learners" controls={controls} onRefresh={reload} />

      <DataTable
        columns={[
          { key: "learner_name", label: "Name" },
          { key: "admission_number", label: "Admission no.", render: (r) => <span className="mono">{r.admission_number}</span> },
          { key: "class_name", label: "Class", render: (r) => r.class_name || "—" },
          { key: "status", label: "Status", render: (r) => statusTag(r.status) },
        ]}
        rows={controls.visibleRows} loading={loading} error={error}
        emptyTitle={controls.query ? "No matching learners" : "No learners yet"}
        emptyHint="Register your first learner to begin."
      />

      {!loading && !error && <TablePagination controls={controls} />}

      {open && (
        <Modal title="Register learner" onClose={() => setOpen(false)}>
          <form onSubmit={save}>
            {formError && <div className="notice error" style={{ marginBottom: "0.75rem" }}>{formError}</div>}
            <div className="form-grid">
              <FormField label="Username"><input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required /></FormField>
              <FormField label="Admission number" hint="Leave blank to generate ADM-SCHOOL-001 automatically."><input value={form.admission_number} onChange={(e) => setForm({ ...form, admission_number: e.target.value })} /></FormField>
              <FormField label="First name"><input value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} required /></FormField>
              <FormField label="Last name"><input value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} required /></FormField>
              <div className="full"><p className="muted">No password is created or shown. After saving, use the password reset flow to let the learner set one.</p></div>
            </div>
            <div className="form-actions">
              <button type="button" className="ghost" onClick={() => setOpen(false)}>Cancel</button>
              <button type="submit" disabled={saving}>{saving ? "Saving…" : "Register"}</button>
            </div>
          </form>
        </Modal>
      )}
    </section>
  );
}
