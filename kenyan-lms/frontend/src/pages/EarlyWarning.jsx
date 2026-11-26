import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { useList, useResource } from "../hooks/useApi";
import { api } from "../services/api";
import useTableControls from "../hooks/useTableControls";
import DataTable from "../components/DataTable";
import Loading from "../components/Loading";
import Modal from "../components/Modal";
import RollingLabel from "../components/RollingLabel";
import StatCard from "../components/StatCard";
import { TableToolbar, TablePagination } from "../components/TableTools";
import { formatDate } from "../utilities/format";

function levelTag(level) {
  const className = level === "HIGH" ? "bad" : level === "MEDIUM" ? "warn" : "info";
  return <span className={`tag ${className}`}>{level}</span>;
}

export default function EarlyWarning() {
  const { user } = useAuth();
  const { push } = useToast();
  const report = useResource("/analytics/early-warning/");
  const tasks = useList("/analytics/interventions/");
  const alertControls = useTableControls(report.data?.alerts || []);
  const taskControls = useTableControls(tasks.data);
  const [selected, setSelected] = useState(null);
  const [busy, setBusy] = useState(false);
  const [level, setLevel] = useState("");

  async function refresh() {
    setBusy(true);
    try {
      const result = await api.post("/analytics/early-warning/refresh/", {});
      push(`${result.tasks_created || 0} new intervention task(s) created.`, "success");
      report.reload();
      tasks.reload();
    } catch (err) {
      push(err.message || "The warning rules could not be recalculated.", "error");
    } finally {
      setBusy(false);
    }
  }

  async function taskAction(id, action, message, body = {}) {
    setBusy(true);
    try {
      await api.post(`/analytics/interventions/${id}/${action}/`, body);
      push(message, "success");
      tasks.reload();
      report.reload();
    } catch (err) {
      push(err.message || "The task could not be updated.", "error");
    } finally {
      setBusy(false);
    }
  }

  if (report.loading || tasks.loading) return <Loading label="Loading early warnings…" />;
  const summary = report.data?.summary || {};
  const rules = report.data?.rules || {};
  const alerts = level
    ? alertControls.filteredRows.filter((row) => row.risk_level === level)
    : alertControls.filteredRows;

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">Student support</div>
          <h1>Early warning</h1>
          <p className="muted">Transparent rules over attendance, results, submissions, progress and fees.</p>
        </div>
        <div className="actions">
          <button
            aria-busy={busy || undefined}
            disabled={busy}
            onClick={refresh}
          >
            {busy ? "Recalculating…" : <RollingLabel>Recalculate warnings</RollingLabel>}
          </button>
        </div>
      </div>

      {(report.error || tasks.error) && (
        <div className="notice error" role="alert">
          {report.error || tasks.error}
        </div>
      )}

      <div className="stat-grid">
        <StatCard label="Learners checked" value={summary.learners_checked ?? "—"} />
        <StatCard label="High risk" value={summary.high ?? 0} />
        <StatCard label="Medium risk" value={summary.medium ?? 0} />
        <StatCard label="Low risk" value={summary.low ?? 0} />
      </div>

      <div className="panel panel-pad" style={{ marginTop: "1.25rem" }}>
        <h2 style={{ marginTop: 0 }}>Rules and thresholds</h2>
        <ul>
          {Object.entries(rules).map(([code, rule]) => (
            <li key={code}>
              <strong>{rule.label}</strong> — {rule.description || `${rule.points} point(s)`}
            </li>
          ))}
        </ul>
        <p className="muted">
          Scores of 1–2 are low, 3–5 medium and 6 or more high. Each alert shows the exact evidence
          behind it, and staff can dismiss a flag without deleting its history.
        </p>
      </div>

      <h2 style={{ marginTop: "1.5rem" }}>Learners to review</h2>
      <TableToolbar
        title="alerts"
        controls={alertControls}
        onRefresh={() => { report.reload(); tasks.reload(); }}
        extra={
          <label className="inline-filter">
            Risk level
            <select value={level} onChange={(event) => setLevel(event.target.value)}>
              <option value="">All</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </label>
        }
      />
      <DataTable
        columns={[
          { key: "learner_name", label: "Learner" },
          { key: "admission_number", label: "Admission no." },
          { key: "class_name", label: "Class", render: (row) => row.class_name || "—" },
          { key: "risk_level", label: "Risk", render: (row) => levelTag(row.risk_level) },
          { key: "risk_score", label: "Score" },
          {
            key: "signals",
            label: "Reasons",
            render: (row) => row.signals.map((signal) => signal.code).join(", "),
          },
          {
            key: "actions",
            label: "Actions",
            render: (row) => (
              <button
                type="button"
                className="ghost small"
                aria-label={`View evidence for ${row.learner_name}`}
                onClick={() => setSelected(row)}
              >
                <RollingLabel>Evidence</RollingLabel>
              </button>
            ),
          },
        ]}
        rows={alerts}
        loading={false}
        error={null}
        emptyTitle={level ? `No ${level.toLowerCase()} risk learners` : "No learners need attention"}
        emptyHint="Alerts appear when the rules find a pattern in existing records."
      />
      <TablePagination controls={alertControls} />

      <h2 style={{ marginTop: "1.5rem" }}>Intervention tasks</h2>
      <DataTable
        columns={[
          { key: "learner_name", label: "Learner" },
          { key: "risk_level", label: "Risk", render: (row) => levelTag(row.risk_level) },
          { key: "status", label: "Status", render: (row) => <span className="tag info">{row.status}</span> },
          { key: "assigned_to_name", label: "Assigned to", render: (row) => row.assigned_to_name || "—" },
          { key: "due_date", label: "Due", render: (row) => formatDate(row.due_date) },
          {
            key: "actions",
            label: "Actions",
            render: (row) => (
              <div className="row-actions">
                {row.status !== "ASSIGNED" && row.status !== "COMPLETED" && (
                  <button
                    type="button"
                    className="secondary small"
                    disabled={busy}
                    aria-label={`Assign ${row.learner_name} to me`}
                    onClick={() => taskAction(row.id, "assign", "Task assigned to you.", { user_id: user?.id })}
                  >
                    <RollingLabel>Assign to me</RollingLabel>
                  </button>
                )}
                {row.status !== "COMPLETED" && row.status !== "DISMISSED" && (
                  <button
                    type="button"
                    className="small"
                    disabled={busy}
                    aria-label={`Complete task for ${row.learner_name}`}
                    onClick={() => taskAction(row.id, "complete", "Task completed.")}
                  >
                    <RollingLabel>Complete</RollingLabel>
                  </button>
                )}
              </div>
            ),
          },
        ]}
        rows={taskControls.visibleRows}
        loading={false}
        error={null}
        emptyTitle="No intervention tasks"
        emptyHint="Recalculate warnings to create follow-up tasks for medium and high risk learners."
      />

      {selected && (
        <Modal title={`Evidence for ${selected.learner_name}`} onClose={() => setSelected(null)}>
          <dl className="detail-list">
            <div><dt>Risk score</dt><dd>{selected.risk_score} ({selected.risk_level})</dd></div>
            <div><dt>Admission number</dt><dd>{selected.admission_number}</dd></div>
            <div><dt>Class</dt><dd>{selected.class_name || "—"}</dd></div>
            <div><dt>Suggested action</dt><dd>{selected.recommended_action || "Review with the learner."}</dd></div>
          </dl>
          <h3>Signals</h3>
          <ul>
            {selected.signals.map((signal) => (
              <li key={signal.code}>
                <strong>{signal.label}</strong> ({signal.points} point(s)) — {signal.detail}
              </li>
            ))}
          </ul>
          <div className="form-actions">
            <button type="button" className="ghost" onClick={() => setSelected(null)}>
              <RollingLabel>Close</RollingLabel>
            </button>
          </div>
        </Modal>
      )}
    </section>
  );
}
