import { useState } from "react";
import { useList } from "../hooks/useApi";
import { api } from "../services/api";
import { useToast } from "../context/ToastContext";
import DataTable from "../components/DataTable";
import Modal from "../components/Modal";
import FormField from "../components/FormField";
import RollingLabel from "../components/RollingLabel";
import HoldToConfirmButton from "../components/HoldToConfirmButton";
import { TableToolbar } from "../components/TableTools";
import useTableControls from "../hooks/useTableControls";

export default function GuardianLinks() {
  const { data, loading, error, reload } = useList("/learners/link-requests/");
  const { push } = useToast();
  const controls = useTableControls(data || []);
  const [decision, setDecision] = useState(null);
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState(null);

  function open(type, row) {
    setDecision({ type, row });
    setNotes("");
    setFormError(null);
  }

  async function save(event) {
    event.preventDefault();
    if (decision.type === "reject" && !notes.trim()) {
      setFormError("Give a short reason for rejecting this link.");
      return;
    }
    setSaving(true);
    setFormError(null);
    try {
      await api.post(`/learners/link-requests/${decision.row.id}/${decision.type}/`, { notes });
      push(`Guardian link ${decision.type === "verify" ? "verified" : "rejected"}.`, "success");
      setDecision(null);
      reload();
    } catch (err) {
      setFormError(err.message || "Something went wrong. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  const pending = (data || []).filter((row) => row.status === "PENDING").length;

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">Family access</div>
          <h1>Guardian links</h1>
          <p className="muted">Learner information opens only after a link has been verified.</p>
        </div>
      </div>

      {pending > 0 && (
        <div className="notice warn" role="status">{pending} link {pending === 1 ? "request is" : "requests are"} awaiting verification.</div>
      )}

      <TableToolbar title="guardian link requests" controls={controls} onRefresh={reload} />
      <DataTable
        columns={[
          { key: "guardian_name", label: "Guardian" },
          { key: "guardian_number", label: "Guardian no.", render: (r) => <span className="mono">{r.guardian_number || "—"}</span> },
          { key: "learner_name", label: "Learner" },
          { key: "admission_number", label: "Admission no.", render: (r) => <span className="mono">{r.admission_number || "—"}</span> },
          { key: "relationship", label: "Relationship" },
          { key: "status", label: "Status", render: (r) => <span className={`tag ${r.status === "VERIFIED" ? "good" : r.status === "REJECTED" ? "bad" : ""}`}>{r.status}</span> },
          { key: "created_at", label: "Requested", render: (r) => (r.created_at || "").slice(0, 10) },
          { key: "_actions", label: "Actions", render: (r) => r.status === "PENDING" ? (
            <div className="row-actions">
              <button
                className="small"
                aria-label={`Verify guardian link for ${r.guardian_name || r.learner_name || "record"}`}
                onClick={() => open("verify", r)}
              >
                Verify
              </button>
              <HoldToConfirmButton
                className="ghost small danger"
                aria-label={`Reject guardian link for ${r.guardian_name || r.learner_name || "record"}`}
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
        emptyTitle="No guardian link requests"
        emptyHint="Requests submitted by guardians appear here for verification."
      />

      {decision && (
        <Modal
          title={decision.type === "verify" ? "Verify guardian link" : "Reject guardian link"}
          onClose={() => setDecision(null)}
        >
          <form onSubmit={save}>
            {formError && <div className="notice error" role="alert">{formError}</div>}
            <p className="muted">
              {decision.row.guardian_name} → {decision.row.learner_name} ({decision.row.admission_number})
            </p>
            <FormField label="Decision notes" hint="A short reason is required when rejecting.">
              <textarea value={notes} onChange={(event) => setNotes(event.target.value)} rows={3} />
            </FormField>
            <div className="form-actions">
              <button type="button" className="ghost" onClick={() => setDecision(null)}><RollingLabel>Cancel</RollingLabel></button>
              <button type="submit" disabled={saving} className={decision.type === "reject" ? "danger" : ""}>
                {saving ? "Saving…" : decision.type === "verify" ? "Verify link" : "Reject link"}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </section>
  );
}
