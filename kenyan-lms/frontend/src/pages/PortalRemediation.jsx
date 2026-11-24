import { useState } from "react";
import { useList } from "../hooks/useApi";
import { api } from "../services/api";
import { useToast } from "../context/ToastContext";
import Loading from "../components/Loading";

const STATUS_LABELS = {
  OPEN: "Suggested",
  ASSIGNED: "Assigned",
  COMPLETED: "Completed",
  DISMISSED: "Dismissed",
};

// Learner-facing view of the same remediation tasks staff see in analytics.
// The API only ever returns tasks linked to the signed-in learner.
export default function PortalRemediation() {
  const tasks = useList("/analytics/my-tasks/");
  const { push } = useToast();
  const [busyId, setBusyId] = useState(null);

  async function updateTask(task, action, message) {
    setBusyId(task.id);
    try {
      await api.post(`/analytics/my-tasks/${task.id}/${action}/`);
      push(message, "success");
      tasks.reload();
    } catch (err) {
      push(err.message, "error");
    } finally {
      setBusyId(null);
    }
  }

  if (tasks.loading) return <Loading />;

  const open = tasks.data.filter((task) => ["OPEN", "ASSIGNED"].includes(task.status));
  const closed = tasks.data.filter((task) => !["OPEN", "ASSIGNED"].includes(task.status));

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">Learning support</div>
          <h1>My support tasks</h1>
        </div>
      </div>
      <div className="notice" style={{ marginBottom: "1rem" }}>
        These suggestions come from your school's assessment and competency evidence.
        They are practice recommendations, not a grade or a KICD decision.
      </div>

      {tasks.error && <div className="notice warn">{tasks.error}</div>}

      <div className="panel panel-pad">
        <h2 style={{ marginTop: 0 }}>Needs attention ({open.length})</h2>
        {!open.length && <p className="muted">No open support tasks right now.</p>}
        <div className="stack">
          {open.map((task) => (
            <article key={task.id} className="notice">
              <div style={{ display: "flex", justifyContent: "space-between", gap: "0.75rem", flexWrap: "wrap" }}>
                <strong>{task.rule_name || task.competency_name || "Recommended practice"}</strong>
                <span className="tag info">{STATUS_LABELS[task.status] || task.status}</span>
              </div>
              <p className="muted" style={{ margin: "0.4rem 0" }}>
                {task.competency_name ? `Competency: ${task.competency_name}. ` : ""}
                {task.due_date ? `Suggested by ${task.due_date}.` : "No due date set."}
              </p>
              <div className="row-actions">
                <button
                  className="small"
                  disabled={busyId === task.id}
                  onClick={() => updateTask(task, "complete", "Task marked complete.")}
                >
                  Mark complete
                </button>
                <button
                  className="ghost small"
                  disabled={busyId === task.id}
                  onClick={() => updateTask(task, "dismiss", "Task dismissed.")}
                >
                  Not needed
                </button>
              </div>
            </article>
          ))}
        </div>
      </div>

      {closed.length > 0 && (
        <div className="panel panel-pad" style={{ marginTop: "1rem" }}>
          <h2 style={{ marginTop: 0 }}>History ({closed.length})</h2>
          <div className="stack">
            {closed.map((task) => (
              <div key={task.id} className="notice success">
                <strong>{task.rule_name || task.competency_name || "Recommended practice"}</strong>{" "}
                <span className="tag">{STATUS_LABELS[task.status] || task.status}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
