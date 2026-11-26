import { useState } from "react";
import { api } from "../services/api";
import { useToast } from "../context/ToastContext";
import FormField from "./FormField";
import RollingLabel from "./RollingLabel";

/**
 * Inline verification of a pending guardian link request. Stays inside the
 * parent dialog so the admin never has to leave the learner/guardian they are
 * working on. All decisions are recorded by the backend audit log.
 */
export default function PendingRequestActions({ request, details, onDecided }) {
  const { push } = useToast();
  const [decision, setDecision] = useState(null);
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  function start(type) {
    setDecision(type);
    setNotes("");
    setError(null);
  }

  async function submit() {
    if (decision === "reject" && !notes.trim()) {
      setError("Give a short reason for rejecting this request.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await api.post(`/learners/link-requests/${request.id}/${decision}/`, {
        notes,
        ...details,
      });
      push(`Link request ${decision === "verify" ? "verified" : "rejected"}.`, "success");
      setDecision(null);
      onDecided?.();
    } catch (err) {
      setError(err.message || "Could not update the link request.");
    } finally {
      setSaving(false);
    }
  }

  if (!decision) {
    return (
      <div className="row-actions">
        <button
          type="button"
          className="small"
          aria-label={`Verify link request ${request.reference || request.id}`}
          onClick={() => start("verify")}
        >
          <RollingLabel>Verify request</RollingLabel>
        </button>
        <button
          type="button"
          className="ghost small danger"
          aria-label={`Reject link request ${request.reference || request.id}`}
          onClick={() => start("reject")}
        >
          <RollingLabel>Reject request</RollingLabel>
        </button>
      </div>
    );
  }

  return (
    <div className="link-decision-form">
      {error && <div className="notice error" role="alert">{error}</div>}
      <FormField label="Decision notes" hint="A short reason is required when rejecting.">
        <textarea
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          rows={2}
          required={decision === "reject"}
        />
      </FormField>
      <div className="form-actions">
        <button type="button" className="ghost small" onClick={() => setDecision(null)}>
          <RollingLabel>Cancel</RollingLabel>
        </button>
        <button
          type="button"
          className={`small ${decision === "reject" ? "danger" : ""}`}
          onClick={submit}
          disabled={saving}
        >
          {saving ? "Saving…" : <RollingLabel>{decision === "verify" ? "Verify link" : "Reject link"}</RollingLabel>}
        </button>
      </div>
    </div>
  );
}
