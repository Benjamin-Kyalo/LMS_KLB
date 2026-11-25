import { useEffect, useState } from "react";
import { useList } from "../hooks/useApi";
import { api, listAll } from "../services/api";
import { useToast } from "../context/ToastContext";
import DataTable from "../components/DataTable";
import Modal from "../components/Modal";
import FormField from "../components/FormField";
import RollingLabel from "../components/RollingLabel";
import HoldToConfirmButton from "../components/HoldToConfirmButton";
import { TableToolbar } from "../components/TableTools";
import useTableControls from "../hooks/useTableControls";

export default function TeacherApprovals() {
  const { data, loading, error, reload } = useList("/teachers/approvals/");
  const { push } = useToast();
  const controls = useTableControls(data || []);
  const [options, setOptions] = useState({ classes: [], subjects: [], years: [] });
  const [decision, setDecision] = useState(null);
  const [form, setForm] = useState({ notes: "", school_class: "", subject: "", academic_year: "" });
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState(null);

  useEffect(() => {
    let active = true;
    Promise.all([
      listAll("/institutions/classes/"),
      listAll("/institutions/subjects/"),
      listAll("/institutions/academic-years/"),
    ]).then(([classes, subjects, years]) => {
      if (active) setOptions({ classes, subjects, years });
    }).catch(() => { /* the form still works without optional assignment data */ });
    return () => { active = false; };
  }, []);

  function open(type, row) {
    setDecision({ type, row });
    setForm({ notes: "", school_class: "", subject: "", academic_year: "" });
    setFormError(null);
  }

  function update(name, value) {
    setForm((previous) => ({ ...previous, [name]: value }));
  }

  async function save(event) {
    event.preventDefault();
    if (decision.type === "reject" && !form.notes.trim()) {
      setFormError("Give a short reason for rejecting this account.");
      return;
    }
    setSaving(true);
    setFormError(null);
    try {
      const payload = { notes: form.notes };
      if (decision.type === "approve") {
        if (form.school_class) payload.school_class = Number(form.school_class);
        if (form.subject) payload.subject = Number(form.subject);
        if (form.academic_year) payload.academic_year = Number(form.academic_year);
      }
      await api.post(`/teachers/approvals/${decision.row.id}/${decision.type}/`, payload);
      push(`Teacher ${decision.type === "approve" ? "approved" : "rejected"}.`, "success");
      setDecision(null);
      reload();
    } catch (err) {
      setFormError(err.details ? JSON.stringify(err.details) : err.message);
    } finally {
      setSaving(false);
    }
  }

  const pending = (data || []).filter((row) => row.status === "PENDING").length;

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">Access control</div>
          <h1>Teacher approvals</h1>
          <p className="muted">Publicly registered teachers stay inactive until you approve them.</p>
        </div>
      </div>

      {pending > 0 && (
        <div className="notice warn" role="status">{pending} teacher {pending === 1 ? "account is" : "accounts are"} awaiting review.</div>
      )}

      <TableToolbar title="teacher approvals" controls={controls} onRefresh={reload} />
      <DataTable
        columns={[
          { key: "teacher_name", label: "Teacher" },
          { key: "email", label: "Email" },
          { key: "employment_type", label: "Employment" },
          { key: "status", label: "Status", render: (r) => <span className={`tag ${r.status === "APPROVED" ? "good" : r.status === "REJECTED" ? "bad" : ""}`}>{r.status}</span> },
          { key: "created_at", label: "Registered", render: (r) => (r.created_at || "").slice(0, 10) },
          { key: "_actions", label: "Actions", render: (r) => r.status === "PENDING" ? (
            <div className="row-actions">
              <button
                className="small"
                aria-label={`Approve teacher account for ${r.teacher_name || r.email || "record"}`}
                onClick={() => open("approve", r)}
              >
                Approve
              </button>
              <HoldToConfirmButton
                className="ghost small danger"
                aria-label={`Reject teacher account for ${r.teacher_name || r.email || "record"}`}
                onConfirm={() => open("reject", r)}
              >
                Reject
              </HoldToConfirmButton>
            </div>
          ) : <span className="muted">Decided</span> },
        ]}
        rows={controls.visibleRows}
        loading={loading}
        error={error}
        emptyTitle="No teacher approvals"
        emptyHint="Teacher accounts created through public registration appear here."
      />

      {decision && (
        <Modal
          title={decision.type === "approve" ? "Approve teacher account" : "Reject teacher account"}
          onClose={() => setDecision(null)}
        >
          <form onSubmit={save}>
            {formError && <div className="notice error" role="alert">{formError}</div>}
            <p className="muted">
              {decision.row.teacher_name} · {decision.row.email || "no email"}
            </p>
            <div className="form-grid">
              <FormField label="Notes" full>
                <textarea value={form.notes} onChange={(event) => update("notes", event.target.value)} rows={3} />
              </FormField>
              {decision.type === "approve" && (
                <>
                  <FormField label="Class (optional)">
                    <select value={form.school_class} onChange={(event) => update("school_class", event.target.value)}>
                      <option value="">— no assignment now —</option>
                      {options.classes.map((item) => <option key={item.id} value={item.id}>{item.name} {item.stream}</option>)}
                    </select>
                  </FormField>
                  <FormField label="Subject (optional)">
                    <select value={form.subject} onChange={(event) => update("subject", event.target.value)}>
                      <option value="">— no assignment now —</option>
                      {options.subjects.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                    </select>
                  </FormField>
                  <FormField label="Academic year (optional)">
                    <select value={form.academic_year} onChange={(event) => update("academic_year", event.target.value)}>
                      <option value="">— no assignment now —</option>
                      {options.years.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                    </select>
                  </FormField>
                  <div className="full"><p className="muted">Provide all three assignment fields together, or leave all three empty.</p></div>
                </>
              )}
            </div>
            <div className="form-actions">
              <button type="button" className="ghost" onClick={() => setDecision(null)}><RollingLabel>Cancel</RollingLabel></button>
              <button type="submit" disabled={saving} className={decision.type === "reject" ? "danger" : ""}>
                {saving ? "Saving…" : decision.type === "approve" ? "Approve account" : "Reject account"}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </section>
  );
}
