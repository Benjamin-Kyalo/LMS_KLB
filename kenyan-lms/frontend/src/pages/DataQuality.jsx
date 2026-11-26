import { useState } from "react";
import { useToast } from "../context/ToastContext";
import { useResource } from "../hooks/useApi";
import { api } from "../services/api";
import HoldToConfirmButton from "../components/HoldToConfirmButton";
import Modal from "../components/Modal";
import RollingLabel from "../components/RollingLabel";

const severityTag = (severity) => (
  <span className={`tag ${severity === "error" ? "bad" : severity === "warning" ? "warn" : "info"}`}>
    {severity}
  </span>
);

export default function DataQuality() {
  const { push } = useToast();
  const scan = useResource("/core/data-quality/");
  const [preview, setPreview] = useState(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  async function showPreview(issue) {
    setBusy(true);
    setMessage("");
    try {
      const result = await api.post("/core/data-quality/fix/", { issue_type: issue.code });
      setPreview({ issue, ...result });
    } catch (err) {
      push(err.message || "The fix could not be previewed.", "error");
    } finally {
      setBusy(false);
    }
  }

  async function applyFix() {
    setBusy(true);
    setMessage("");
    try {
      const result = await api.post("/core/data-quality/fix/", {
        issue_type: preview.code,
        confirm: true,
      });
      setMessage(`${result.applied ? "Applied" : "Checked"} ${result.change_count} change(s).`);
      push(`${result.change_count} record(s) updated and audited.`, "success");
      setPreview(null);
      scan.reload();
    } catch (err) {
      setMessage(err.message || "The fix could not be applied.");
      push(err.message || "The fix could not be applied.", "error");
    } finally {
      setBusy(false);
    }
  }

  const issues = scan.data?.issues || [];

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">Record hygiene</div>
          <h1>Data quality</h1>
          <p className="muted">Read-only scans with a small, audited set of safe fixes. No records are deleted here.</p>
        </div>
        <div className="actions">
          <button
            className="secondary"
            disabled={busy}
            aria-busy={busy || undefined}
            onClick={() => scan.reload()}
          >
            {busy ? "Refreshing…" : <RollingLabel>Run scan</RollingLabel>}
          </button>
        </div>
      </div>

      {scan.error && <div className="notice error" role="alert">{scan.error}</div>}
      {message && <div className="notice success" role="status">{message}</div>}

      <div className="notice info">
        Only whitespace in identifiers and missing admission dates can be fixed automatically.
        Every fix shows a preview first and writes an audit entry with the old and new values.
      </div>

      {scan.loading ? (
        <p className="muted" role="status">Scanning records…</p>
      ) : (
        <div className="panel">
          <table className="data">
            <thead>
              <tr>
                <th scope="col">Check</th>
                <th scope="col">Severity</th>
                <th scope="col">Count</th>
                <th scope="col">Examples</th>
                <th scope="col">Actions</th>
              </tr>
            </thead>
            <tbody>
              {issues.map((issue) => (
                <tr key={issue.code}>
                  <td>
                    <strong>{issue.label}</strong>
                    {issue.detail && <div className="muted">{issue.detail}</div>}
                  </td>
                  <td>{severityTag(issue.severity)}</td>
                  <td>{issue.count}</td>
                  <td>{issue.samples.length ? issue.samples.join(", ") : "—"}</td>
                  <td>
                    {issue.fixable && issue.count ? (
                      <button
                        type="button"
                        className="ghost small"
                        disabled={busy}
                        aria-label={`Preview fix for ${issue.label}`}
                        onClick={() => showPreview(issue)}
                      >
                        <RollingLabel>Preview fix</RollingLabel>
                      </button>
                    ) : (
                      <span className="muted">Review manually</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {preview && (
        <Modal title={`Fix: ${preview.issue.label}`} onClose={() => setPreview(null)}>
          <p>{preview.description}</p>
          <p className="muted">{preview.change_count} change(s) will be applied in one transaction.</p>
          {preview.changes.length > 0 && (
            <table className="data">
              <thead>
                <tr>
                  <th scope="col">Record</th>
                  <th scope="col">Field</th>
                  <th scope="col">Before</th>
                  <th scope="col">After</th>
                </tr>
              </thead>
              <tbody>
                {preview.changes.map((change, index) => (
                  <tr key={`${change.entity_type}-${change.entity_id}-${change.field}-${index}`}>
                    <td>{change.entity_type} #{change.entity_id}</td>
                    <td className="mono">{change.field}</td>
                    <td>{String(change.before ?? "—")}</td>
                    <td>{String(change.after ?? "—")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {message && <div className="notice error" role="alert">{message}</div>}
          <div className="form-actions">
            <button type="button" className="ghost" onClick={() => setPreview(null)}>
              <RollingLabel>Cancel</RollingLabel>
            </button>
            <HoldToConfirmButton
              className="danger"
              title={`Apply ${preview.issue.label} fix`}
              disabled={busy || !preview.change_count}
              onConfirm={applyFix}
            >
              {`Apply ${preview.change_count} fix(es)`}
            </HoldToConfirmButton>
          </div>
        </Modal>
      )}
    </section>
  );
}
