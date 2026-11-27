import { useState } from "react";
import { ClipboardCheck, Send, UserRound } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { useList } from "../hooks/useApi";
import useTableControls from "../hooks/useTableControls";
import { api } from "../services/api";
import { canWriteTeaching } from "../utilities/roles";
import { formatDateTime } from "../utilities/format";
import DataTable from "../components/DataTable";
import Modal from "../components/Modal";
import RollingLabel from "../components/RollingLabel";
import RubricGradingDialog from "../components/RubricGradingDialog";
import { DialogLead, DialogSection } from "../components/DialogParts";
import { TablePagination, TableToolbar } from "../components/TableTools";

function statusTag(row) {
  const tone = row.status === "RETURNED" ? "info"
    : row.status === "GRADED" ? "good"
      : row.status === "DRAFT" ? "" : "warn";
  return <span className={`tag ${tone}`}>{row.status || "—"}</span>;
}

export default function Submissions() {
  const { user } = useAuth();
  const { push } = useToast();
  const { data, loading, error, reload } = useList("/courses/submissions/");
  const controls = useTableControls(data);
  const [detail, setDetail] = useState(null);
  const [grading, setGrading] = useState(null);
  const [publishing, setPublishing] = useState(null);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState(null);
  const canGrade = canWriteTeaching(user);

  async function publish() {
    const submission = publishing;
    setBusy(true);
    setActionError(null);
    try {
      await api.post(`/courses/submissions/${submission.id}/publish-feedback/`);
      push("Feedback published to the learner and permitted guardians.", "success");
      setPublishing(null);
      setDetail(null);
      await reload();
    } catch (err) {
      setActionError(err.message || "Feedback could not be published.");
    } finally {
      setBusy(false);
    }
  }

  async function afterGrade() {
    setGrading(null);
    setDetail(null);
    await reload();
  }

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">Learning management</div>
          <h1>Submissions</h1>
          <p>Mark work with a rubric or a direct score, then publish feedback when it is ready.</p>
        </div>
      </div>

      <div className="notice info dialog-error" role="note">
        Grades stay private inside the school until you publish them. Publication notifies the learner and
        guardians whose academic access is enabled.
      </div>

      <TableToolbar title="submissions" controls={controls} onRefresh={reload} />

      <DataTable
        columns={[
          { key: "learner_name", label: "Learner", render: (r) => `${r.learner_name || "—"}${r.admission_number ? ` · ${r.admission_number}` : ""}` },
          { key: "assignment_title", label: "Assignment" },
          { key: "submitted_at", label: "Submitted", render: (r) => formatDateTime(r.submitted_at) },
          { key: "status", label: "Status", render: statusTag },
          { key: "score", label: "Score", render: (r) => r.score ?? "—" },
          { key: "rubric_name", label: "Rubric", render: (r) => r.rubric_name || "Direct score" },
          { key: "feedback_published_at", label: "Feedback", render: (r) => r.feedback_published_at ? <span className="tag good">Published</span> : <span className="tag warn">Private</span> },
          { key: "_actions", label: "Actions", render: (r) => (
            <div className="row-actions">
              <button className="ghost small" aria-label={`View submission from ${r.learner_name || "learner"}`} onClick={() => setDetail(r)}><RollingLabel>View</RollingLabel></button>
              {canGrade && (
                <>
                  <button className="small" aria-label={`Grade submission from ${r.learner_name || "learner"}`} onClick={() => setGrading(r)}><RollingLabel>Grade</RollingLabel></button>
                  {r.graded_at && !r.feedback_published_at && (
                    <button
                      className="secondary small"
                      aria-label={`Publish feedback for ${r.learner_name || "learner"}`}
                      onClick={() => { setActionError(null); setPublishing(r); }}
                    >
                      <RollingLabel>Publish feedback</RollingLabel>
                    </button>
                  )}
                </>
              )}
            </div>
          ) },
        ]}
        rows={controls.visibleRows}
        loading={loading}
        error={error}
        emptyTitle="No submissions yet"
        emptyHint="Learner submissions appear here once assignments are published."
      />
      {!loading && !error && <TablePagination controls={controls} />}

      {detail && (
        <Modal title="Submission details" onClose={() => setDetail(null)}>
          <DialogLead icon={UserRound} kicker="Submission record">
            {detail.learner_name || "Learner"} · {detail.assignment_title || "Assignment"} · attempt {detail.current_attempt || 1}
          </DialogLead>
          <DialogSection title="Submitted work">
            <p className="muted" style={{ whiteSpace: "pre-wrap" }}>{detail.text_answer || "No written answer was provided."}</p>
            {detail.attachment && <p><a href={detail.attachment} target="_blank" rel="noreferrer">Open attachment</a></p>}
          </DialogSection>
          {detail.achievement_level && (
            <DialogSection title="Achievement" hint="Resolved from the rubric band for the final percentage.">
              <p><strong>{detail.achievement_level}</strong> · {detail.score} / {detail.assignment_max_score}</p>
            </DialogSection>
          )}
          {(detail.criterion_scores || []).length > 0 && (
            <DialogSection title="Criterion scores">
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
            </DialogSection>
          )}
          {(detail.attempts || []).length > 0 && (
            <DialogSection title="Attempt history" hint="Each resubmission keeps the earlier answer and grade.">
              <ol className="compact-list">
                {detail.attempts.map((attempt) => (
                  <li key={attempt.id}>
                    <strong>Attempt {attempt.attempt_number}</strong> · submitted {formatDateTime(attempt.submitted_at)}
                    {attempt.score !== null && ` · ${attempt.score} / ${detail.assignment_max_score}`}
                    {attempt.feedback ? <p className="muted">{attempt.feedback}</p> : null}
                  </li>
                ))}
              </ol>
            </DialogSection>
          )}
          <div className="dialog-actions">
            {canGrade && detail.graded_at && !detail.feedback_published_at && (
              <button
                type="button"
                className="secondary"
                onClick={() => { setActionError(null); setPublishing(detail); }}
              >
                <RollingLabel>Publish feedback</RollingLabel>
              </button>
            )}
            <button type="button" className="ghost" onClick={() => setDetail(null)}><RollingLabel>Close</RollingLabel></button>
          </div>
        </Modal>
      )}

      {publishing && (
        <Modal title="Publish feedback" onClose={() => setPublishing(null)}>
          <DialogLead icon={Send} tone="info" kicker="Feedback release">
            Publish the grade and written feedback for <strong>{publishing.learner_name || "this learner"}</strong>?
          </DialogLead>
          <DialogSection title="Who will be notified">
            <ol className="dialog-steps">
              <li>The learner sees the grade in the portal.</li>
              <li>Verified guardians with academic access receive a notification.</li>
              <li>Private staff notes remain hidden.</li>
            </ol>
          </DialogSection>
          {actionError && <div className="notice error dialog-error" role="alert">{actionError}</div>}
          <div className="dialog-actions">
            <button type="button" className="ghost" onClick={() => setPublishing(null)}><RollingLabel>Cancel</RollingLabel></button>
            <button type="button" onClick={publish} disabled={busy} aria-busy={busy || undefined}>
              {busy ? "Publishing…" : <RollingLabel>Publish feedback</RollingLabel>}
            </button>
          </div>
        </Modal>
      )}

      {grading && <RubricGradingDialog submission={grading} onClose={() => setGrading(null)} onSaved={afterGrade} />}
    </section>
  );
}
