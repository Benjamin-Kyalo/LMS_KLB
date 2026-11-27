import { useState } from "react";
import { RotateCcw, UserRound } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { useList } from "../hooks/useApi";
import useTableControls from "../hooks/useTableControls";
import { api } from "../services/api";
import { isLearner } from "../utilities/roles";
import { formatDateTime } from "../utilities/format";
import DataTable from "../components/DataTable";
import FormField from "../components/FormField";
import Modal from "../components/Modal";
import RollingLabel from "../components/RollingLabel";
import { DialogLead, DialogSection } from "../components/DialogParts";
import { TablePagination, TableToolbar } from "../components/TableTools";

function statusTag(row) {
  const tone = row.status === "RETURNED" ? "info"
    : row.status === "GRADED" ? "good"
      : row.status === "DRAFT" ? "" : "warn";
  return <span className={`tag ${tone}`}>{row.status || "—"}</span>;
}

export default function PortalSubmissions() {
  const { user } = useAuth();
  const { push } = useToast();
  const { data, loading, error, reload } = useList("/courses/submissions/");
  const controls = useTableControls(data);
  const [detail, setDetail] = useState(null);
  const [resubmitting, setResubmitting] = useState(null);
  const [answer, setAnswer] = useState("");
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState(null);

  function openResubmit(row) {
    setResubmitting(row);
    setAnswer(row.text_answer || "");
    setFile(null);
    setActionError(null);
  }

  async function resubmit(event) {
    event.preventDefault();
    if (!answer.trim() && !file) {
      setActionError("Add an answer or choose a file before resubmitting.");
      return;
    }
    setBusy(true);
    setActionError(null);
    try {
      const path = `/courses/submissions/${resubmitting.id}/resubmit/`;
      if (file) {
        const body = new FormData();
        body.append("text_answer", answer);
        body.append("attachment", file);
        await api.upload(path, body, "POST");
      } else {
        await api.post(path, { text_answer: answer });
      }
      push("New attempt submitted.", "success");
      setResubmitting(null);
      setDetail(null);
      await reload();
    } catch (err) {
      setActionError(err.message || "The resubmission could not be saved.");
    } finally {
      setBusy(false);
    }
  }

  const canResubmit = (row) => isLearner(user)
    && row.allow_resubmission
    && row.current_attempt < row.max_attempts;

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">Learning</div>
          <h1>My submissions</h1>
          <p>Read returned feedback and, where allowed, send a new attempt.</p>
        </div>
      </div>

      <div className="notice info dialog-error" role="note">
        Feedback appears only after a teacher publishes it. Private staff notes are never shown here.
      </div>

      <TableToolbar title="submissions" controls={controls} onRefresh={reload} />

      <DataTable
        columns={[
          { key: "assignment_title", label: "Assignment" },
          { key: "learner_name", label: "Learner", render: (r) => isLearner(user) ? "You" : (r.learner_name || "—") },
          { key: "submitted_at", label: "Submitted", render: (r) => formatDateTime(r.submitted_at) },
          { key: "status", label: "Status", render: statusTag },
          { key: "score", label: "Score", render: (r) => r.feedback_published_at ? `${r.score ?? "—"} / ${r.assignment_max_score ?? "—"}` : "Pending release" },
          { key: "_actions", label: "Actions", render: (r) => (
            <div className="row-actions">
              <button className="ghost small" aria-label={`View feedback for ${r.assignment_title || "assignment"}`} onClick={() => setDetail(r)}><RollingLabel>View</RollingLabel></button>
              {canResubmit(r) && (
                <button
                  className="small"
                  aria-label={`Resubmit ${r.assignment_title || "assignment"}`}
                  onClick={() => openResubmit(r)}
                >
                  <RollingLabel>Resubmit</RollingLabel>
                </button>
              )}
            </div>
          ) },
        ]}
        rows={controls.visibleRows}
        loading={loading}
        error={error}
        emptyTitle="No submissions yet"
        emptyHint="Submit an assignment to see its feedback here."
      />
      {!loading && !error && <TablePagination controls={controls} />}

      {detail && (
        <Modal title="Assignment feedback" onClose={() => setDetail(null)}>
          <DialogLead icon={UserRound} kicker={detail.learner_name || "Submission"}>
            {detail.assignment_title || "Assignment"} · attempt {detail.current_attempt || 1}
          </DialogLead>
          <DialogSection title="Your answer">
            <p className="muted" style={{ whiteSpace: "pre-wrap" }}>{detail.text_answer || "No written answer was provided."}</p>
          </DialogSection>
          {detail.feedback_published_at ? (
            <DialogSection title="Teacher feedback" hint={`Published ${formatDateTime(detail.feedback_published_at)}`}>
              <p><strong>{detail.achievement_level ? `${detail.achievement_level} · ` : ""}{detail.score ?? "—"} / {detail.assignment_max_score ?? "—"}</strong></p>
              <p className="muted" style={{ whiteSpace: "pre-wrap" }}>{detail.feedback || "No written comment was added."}</p>
              {(detail.criterion_scores || []).length > 0 && (
                <table className="data">
                  <thead><tr><th scope="col">Criterion</th><th scope="col">Score</th><th scope="col">Comment</th></tr></thead>
                  <tbody>
                    {detail.criterion_scores.map((row) => (
                      <tr key={row.id}>
                        <td>{row.criterion_name}</td>
                        <td>{row.score} / {row.max_score}</td>
                        <td>{row.comment || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </DialogSection>
          ) : (
            <DialogSection title="Teacher feedback">
              <p className="muted">Your teacher has saved this work but has not released feedback yet.</p>
            </DialogSection>
          )}
          {(detail.attempts || []).length > 0 && (
            <DialogSection title="Attempt history">
              <ol className="compact-list">
                {detail.attempts.map((attempt) => (
                  <li key={attempt.id}>
                    <strong>Attempt {attempt.attempt_number}</strong> · {formatDateTime(attempt.submitted_at)}
                  </li>
                ))}
              </ol>
            </DialogSection>
          )}
          <div className="dialog-actions">
            {canResubmit(detail) && (
              <button type="button" onClick={() => openResubmit(detail)}><RollingLabel>Resubmit</RollingLabel></button>
            )}
            <button type="button" className="ghost" onClick={() => setDetail(null)}><RollingLabel>Close</RollingLabel></button>
          </div>
        </Modal>
      )}

      {resubmitting && (
        <Modal title="Resubmit assignment" onClose={() => setResubmitting(null)}>
          <form onSubmit={resubmit}>
            <DialogLead icon={RotateCcw} tone="info" kicker={`Attempt ${resubmitting.current_attempt + 1}`}>
              Send a fresh answer for <strong>{resubmitting.assignment_title || "this assignment"}</strong>.
              The earlier attempt is kept in your history.
            </DialogLead>
            {actionError && <div className="notice error dialog-error" role="alert">{actionError}</div>}
            <DialogSection title="New answer" hint="Add written work, attach a file, or both.">
              <div className="form-grid">
                <FormField label="Answer" full>
                  <textarea rows={5} value={answer} onChange={(e) => setAnswer(e.target.value)} />
                </FormField>
                <FormField label="Attachment" hint="Optional. Choose a file to replace the earlier upload." full>
                  <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} />
                </FormField>
              </div>
            </DialogSection>
            <div className="dialog-actions">
              <button type="button" className="ghost" onClick={() => setResubmitting(null)}><RollingLabel>Cancel</RollingLabel></button>
              <button type="submit" disabled={busy} aria-busy={busy || undefined}>
                {busy ? "Sending…" : <RollingLabel>Send new attempt</RollingLabel>}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </section>
  );
}
