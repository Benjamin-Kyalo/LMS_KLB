import { useState } from "react";
import { Link } from "react-router-dom";
import { useList, useResource } from "../hooks/useApi";
import { api } from "../services/api";
import { useToast } from "../context/ToastContext";
import { useAuth } from "../context/AuthContext";
import { canWriteContent } from "../utilities/roles";
import DataTable from "../components/DataTable";
import Modal from "../components/Modal";
import FormField from "../components/FormField";
import RollingLabel from "../components/RollingLabel";
import { statusTag } from "../utilities/format";

const REVIEWABLE = new Set(["SUBMITTED", "UNDER_REVIEW"]);
const PUBLISHABLE = new Set(["APPROVED"]);
const SUBMITTABLE = new Set(["DRAFT", "REJECTED", "CHANGES_REQUESTED"]);

// Internal review workflow. It never contacts KICD or claims official approval.
export default function ApprovalRequests() {
  const { user } = useAuth();
  const { push } = useToast();
  const curator = canWriteContent(user);
  const { data, loading, error, reload } = useList("/approval/requests/");
  const summary = useResource("/approval/requests/summary/");
  const [review, setReview] = useState(null);
  const [decision, setDecision] = useState("APPROVE");
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);

  async function act(row, action, body) {
    setBusy(true);
    try {
      await api.post(`/approval/requests/${row.id}/${action}/`, body || {});
      push(`Request ${action}ed.`, "success");
      setReview(null);
      setNotes("");
      reload();
      summary.reload();
    } catch (err) {
      push(err.details ? JSON.stringify(err.details) : err.message, "error");
    } finally {
      setBusy(false);
    }
  }

  const columns = [
    { key: "reference", label: "Reference", render: (r) => <span className="mono">{r.reference}</span> },
    { key: "title", label: "Title" },
    { key: "content_type", label: "Type", render: (r) => String(r.content_type || "—").replace(/_/g, " ") },
    { key: "status", label: "Status", render: (r) => statusTag(r.status) },
    {
      key: "_actions", label: "Actions", render: (row) => (
        <div className="row-actions">
          {SUBMITTABLE.has(row.status) && <button className="ghost small" aria-label={`Submit ${row.title || row.reference || "request"}`} disabled={busy} onClick={() => act(row, "submit")}><RollingLabel>Submit</RollingLabel></button>}
          {curator && REVIEWABLE.has(row.status) && <button className="ghost small" aria-label={`Review ${row.title || row.reference || "request"}`} disabled={busy} onClick={() => { setReview(row); setDecision("APPROVE"); setNotes(""); }}><RollingLabel>Review</RollingLabel></button>}
          {curator && PUBLISHABLE.has(row.status) && <button className="ghost small" aria-label={`Publish ${row.title || row.reference || "request"}`} disabled={busy} onClick={() => act(row, "publish")}><RollingLabel>Publish</RollingLabel></button>}
          {!SUBMITTABLE.has(row.status) && !REVIEWABLE.has(row.status) && !PUBLISHABLE.has(row.status) && <span className="muted">—</span>}
        </div>
      ),
    },
  ];

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">Publishing quality assurance</div>
          <h1>Approval requests</h1>
        </div>
        <div className="actions">
          <Link className="button-link secondary" to="/admin/approval/checklist">Checklist items</Link>
          <Link className="button-link secondary" to="/admin/approval/decisions">Decisions</Link>
        </div>
      </div>

      <div className="notice" style={{ marginBottom: "1rem" }}>
        KICD-style internal review. This workflow records your school's own checks; it does not
        submit anything to KICD and does not represent official KICD approval.
      </div>

      <div className="stat-grid">
        <div className="stat"><div className="num">{summary.data?.total ?? "—"}</div><div className="label">Total requests</div></div>
        <div className="stat"><div className="num">{summary.data?.by_status?.SUBMITTED ?? 0}</div><div className="label">Awaiting review</div></div>
        <div className="stat"><div className="num">{summary.data?.by_status?.APPROVED ?? 0}</div><div className="label">Approved</div></div>
        <div className="stat"><div className="num">{summary.data?.by_status?.PUBLISHED ?? 0}</div><div className="label">Published</div></div>
      </div>

      <div style={{ marginTop: "1.2rem" }}>
        <DataTable
          columns={columns}
          rows={data}
          loading={loading}
          error={error}
          emptyTitle="No approval requests yet"
          emptyHint="Create a request from a textbook or learning resource to begin the review."
        />
      </div>

      {review && (
        <Modal title={`Review ${review.reference}`} onClose={() => setReview(null)}>
          <form onSubmit={(e) => { e.preventDefault(); act(review, "review", { decision, notes }); }}>
            {review.error && <div className="notice error" role="alert">{review.error}</div>}
            <div className="form-grid">
              <FormField label="Decision">
                <select value={decision} onChange={(e) => setDecision(e.target.value)}>
                  <option value="APPROVE">Approve</option>
                  <option value="REJECT">Reject</option>
                  <option value="REQUEST_CHANGES">Request changes</option>
                </select>
              </FormField>
              <FormField label="Notes" full>
                <textarea rows={4} value={notes} onChange={(e) => setNotes(e.target.value)} />
              </FormField>
            </div>
            <div className="form-actions">
              <button type="button" className="ghost" onClick={() => setReview(null)}><RollingLabel>Cancel</RollingLabel></button>
              <button type="submit" disabled={busy}>{busy ? "Saving…" : <RollingLabel>Record decision</RollingLabel>}</button>
            </div>
          </form>
        </Modal>
      )}
    </section>
  );
}
