import { useEffect, useMemo, useState } from "react";
import { ClipboardCheck } from "lucide-react";
import { api, listAll } from "../services/api";
import { useToast } from "../context/ToastContext";
import FormField from "./FormField";
import Modal from "./Modal";
import RollingLabel from "./RollingLabel";
import { DialogLead, DialogSection } from "./DialogParts";

function asNumber(value) {
  if (value === "" || value === null || value === undefined) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export default function RubricGradingDialog({ submission, onClose, onSaved }) {
  const { push } = useToast();
  const [rubric, setRubric] = useState(null);
  const [criteria, setCriteria] = useState([]);
  const [comments, setComments] = useState([]);
  const [scores, setScores] = useState({});
  const [feedback, setFeedback] = useState(submission.feedback || "");
  const [privateNotes, setPrivateNotes] = useState(submission.private_notes || "");
  const [directScore, setDirectScore] = useState(submission.score ?? "");
  const [selectedComment, setSelectedComment] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      try {
        if (!submission.rubric) {
          if (active) setLoading(false);
          return;
        }
        const [rubricData, criteriaData, commentData] = await Promise.all([
          api.get(`/curriculum/rubrics/${submission.rubric}/`),
          listAll(`/curriculum/rubric-criteria/?rubric=${submission.rubric}`),
          listAll("/curriculum/feedback-comments/"),
        ]);
        if (!active) return;
        setRubric(rubricData);
        setCriteria(criteriaData);
        setComments(commentData);
        const existing = {};
        (submission.criterion_scores || []).forEach((row) => {
          existing[row.criterion] = { score: row.score, comment: row.comment || "" };
        });
        setScores(existing);
      } catch (err) {
        if (active) setError(err.message || "The rubric could not be loaded.");
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => { active = false; };
  }, [submission]);

  const total = useMemo(() => criteria.reduce((sum, criterion) => {
    const score = asNumber(scores[criterion.id]?.score);
    return sum + (score || 0);
  }, 0), [criteria, scores]);
  const maxScore = asNumber(submission.assignment_max_score) || 100;

  function setCriterion(id, field, value) {
    setScores((previous) => ({
      ...previous,
      [id]: { ...(previous[id] || { score: "", comment: "" }), [field]: value },
    }));
  }

  function addPhrase() {
    const phrase = comments.find((row) => String(row.id) === String(selectedComment))?.text;
    if (!phrase) return;
    setFeedback((previous) => (previous ? `${previous.trim()} ${phrase}` : phrase));
    setSelectedComment("");
  }

  function validate() {
    if (rubric) {
      if (criteria.length === 0) return "Add at least one criterion to this rubric before grading.";
      for (const criterion of criteria) {
        const score = asNumber(scores[criterion.id]?.score);
        const maximum = asNumber(criterion.max_score);
        if (score === null) return `Enter a score for ${criterion.name}.`;
        if (score < 0 || (maximum !== null && score > maximum)) {
          return `${criterion.name} must be between 0 and ${maximum}.`;
        }
      }
      if (total > maxScore) return `The total cannot exceed the assignment maximum of ${maxScore}.`;
    } else {
      const score = asNumber(directScore);
      if (score === null || score < 0 || score > maxScore) {
        return `Enter a score between 0 and ${maxScore}.`;
      }
    }
    return null;
  }

  async function submit(event) {
    event.preventDefault();
    const problem = validate();
    if (problem) {
      setError(problem);
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const path = `/courses/submissions/${submission.id}/`;
      const payload = rubric
        ? {
            criteria: criteria.map((criterion) => ({
              criterion: criterion.id,
              score: String(asNumber(scores[criterion.id].score)),
              comment: scores[criterion.id].comment || "",
            })),
            overall_feedback: feedback,
            private_notes: privateNotes,
          }
        : { score: String(asNumber(directScore)), feedback };
      await api.post(`${path}${rubric ? "grade-rubric/" : "grade/"}`, payload);
      push("Grade saved. Publish feedback when it is ready.", "success");
      onSaved();
    } catch (err) {
      setError(err.message || "The grade could not be saved.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title={`Grade ${submission.learner_name || "submission"}`} onClose={onClose}>
      <form onSubmit={submit}>
        <DialogLead icon={ClipboardCheck} kicker="Assessment marking">
          Save a grade and written feedback. The learner and guardians see nothing until feedback is published.
        </DialogLead>
        {error && <div className="notice error dialog-error" role="alert">{error}</div>}
        {loading ? (
          <div className="notice info" role="status">Loading the marking grid…</div>
        ) : (
          <>
            <DialogSection
              title={rubric ? `${rubric.name} marking grid` : "Direct score"}
              hint={rubric
                ? `Assignment maximum: ${maxScore}. Each criterion has its own limit.`
                : `This assignment has no rubric. Score out of ${maxScore}.`}
            >
              {rubric ? (
                <div style={{ overflowX: "auto" }}>
                  <table className="data">
                    <thead>
                      <tr>
                        <th scope="col">Criterion</th>
                        <th scope="col">Maximum</th>
                        <th scope="col">Score</th>
                        <th scope="col">Comment</th>
                      </tr>
                    </thead>
                    <tbody>
                      {criteria.map((criterion) => (
                        <tr key={criterion.id}>
                          <td>{criterion.name}</td>
                          <td>{criterion.max_score}</td>
                          <td>
                            <label className="sr-only" htmlFor={`criterion-${criterion.id}`}>
                              Score for {criterion.name}
                            </label>
                            <input
                              id={`criterion-${criterion.id}`}
                              type="number"
                              min="0"
                              max={criterion.max_score}
                              step="0.01"
                              value={scores[criterion.id]?.score ?? ""}
                              onChange={(e) => setCriterion(criterion.id, "score", e.target.value)}
                              required
                            />
                          </td>
                          <td>
                            <label className="sr-only" htmlFor={`criterion-comment-${criterion.id}`}>
                              Comment for {criterion.name}
                            </label>
                            <input
                              id={`criterion-comment-${criterion.id}`}
                              value={scores[criterion.id]?.comment ?? ""}
                              onChange={(e) => setCriterion(criterion.id, "comment", e.target.value)}
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr><th scope="row" colSpan="2">Total</th><td colSpan="2"><strong>{total} / {maxScore}</strong></td></tr>
                    </tfoot>
                  </table>
                </div>
              ) : (
                <FormField label="Score">
                  <input
                    type="number"
                    min="0"
                    max={maxScore}
                    step="0.01"
                    value={directScore}
                    onChange={(e) => setDirectScore(e.target.value)}
                    required
                  />
                </FormField>
              )}
            </DialogSection>

            <DialogSection title="Written feedback" hint="Published with the grade after you choose Publish feedback.">
              {comments.length > 0 && (
                <div className="form-grid" style={{ marginBottom: "0.6rem" }}>
                  <FormField label="Insert a saved comment">
                    <select value={selectedComment} onChange={(e) => setSelectedComment(e.target.value)}>
                      <option value="">— choose a phrase —</option>
                      {comments.map((comment) => (
                        <option key={comment.id} value={comment.id}>{comment.text}</option>
                      ))}
                    </select>
                  </FormField>
                  <div style={{ display: "flex", alignItems: "flex-end" }}>
                    <button type="button" className="secondary" onClick={addPhrase} disabled={!selectedComment}>
                      <RollingLabel>Add phrase</RollingLabel>
                    </button>
                  </div>
                </div>
              )}
              <FormField label="Feedback for the learner" full>
                <textarea rows={4} value={feedback} onChange={(e) => setFeedback(e.target.value)} />
              </FormField>
              <FormField label="Private notes for staff" hint="Never shown to learners or guardians." full>
                <textarea rows={3} value={privateNotes} onChange={(e) => setPrivateNotes(e.target.value)} />
              </FormField>
            </DialogSection>
          </>
        )}
        <div className="dialog-actions">
          <button type="button" className="ghost" onClick={onClose}><RollingLabel>Cancel</RollingLabel></button>
          <button type="submit" disabled={busy || loading} aria-busy={busy || undefined}>
            {busy ? "Saving grade…" : <RollingLabel>Save grade</RollingLabel>}
          </button>
        </div>
      </form>
    </Modal>
  );
}
