import { useState } from "react";
import { Link } from "react-router-dom";
import { useResource } from "../hooks/useApi";
import { api } from "../services/api";
import { useToast } from "../context/ToastContext";
import { isAdmin, canWriteTeaching } from "../utilities/roles";
import { useAuth } from "../context/AuthContext";
import StatCard from "../components/StatCard";
import DataTable from "../components/DataTable";
import Loading from "../components/Loading";
import RollingLabel from "../components/RollingLabel";

const percent = (value) => (value === null || value === undefined ? "—" : `${Number(value).toFixed(1)}%`);

export default function AnalyticsOverview() {
  const { user } = useAuth();
  const { push } = useToast();
  const dashboard = useResource("/analytics/dashboard/");
  const cohorts = useResource("/analytics/cohorts/");
  const remediation = useResource("/analytics/remediation/summary/");
  const snapshots = useResource("/analytics/snapshots/");
  const [busyAction, setBusyAction] = useState("");

  async function post(path, message, action) {
    setBusyAction(action);
    try {
      await api.post(path, {});
      push(message, "success");
      dashboard.reload(); cohorts.reload(); remediation.reload(); snapshots.reload();
    } catch (err) {
      push(err.details ? JSON.stringify(err.details) : err.message, "error");
    } finally {
      setBusyAction("");
    }
  }

  if (dashboard.loading || cohorts.loading || remediation.loading) return <Loading />;
  const kpis = dashboard.data || {};
  const rows = Array.isArray(cohorts.data) ? cohorts.data : (cohorts.data?.results || []);
  const counts = remediation.data?.by_status || remediation.data || {};

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">School intelligence</div>
          <h1>Analytics &amp; remediation</h1>
        </div>
        <div className="actions">
          <Link className="button-link secondary" to="/admin/analytics/rules"><RollingLabel>Rules</RollingLabel></Link>
          <Link className="button-link secondary" to="/admin/analytics/tasks"><RollingLabel>Tasks</RollingLabel></Link>
          <Link className="button-link secondary" to="/admin/analytics/snapshots"><RollingLabel>Snapshots</RollingLabel></Link>
          {canWriteTeaching(user) && (
            <button
              aria-busy={busyAction === "evaluate" || undefined}
              disabled={Boolean(busyAction)}
              onClick={() => post("/analytics/remediation/evaluate/", "Remediation evaluated.", "evaluate")}
            >
              {busyAction === "evaluate" ? "Evaluating…" : <RollingLabel>Evaluate now</RollingLabel>}
            </button>
          )}
          {isAdmin(user) && (
            <button
              className="secondary"
              aria-busy={busyAction === "snapshot" || undefined}
              disabled={Boolean(busyAction)}
              onClick={() => post("/analytics/snapshots/refresh/", "Snapshot refreshed.", "snapshot")}
            >
              {busyAction === "snapshot" ? "Refreshing…" : <RollingLabel>Refresh snapshot</RollingLabel>}
            </button>
          )}
        </div>
      </div>

      <div className="notice" style={{ marginBottom: "1rem" }}>
        Aggregation over existing school records. This is not a data warehouse product and no
        model is trained here; computed snapshots are stored locally for reporting.
      </div>

      {(dashboard.error || cohorts.error || remediation.error) && (
        <div className="notice error" role="alert" style={{ marginBottom: "1rem" }}>
          {dashboard.error || cohorts.error || remediation.error}
        </div>
      )}

      <div className="stat-grid">
        <StatCard label="Learners" value={kpis.total_learners ?? kpis.learners ?? "—"} />
        <StatCard label="Average attendance" value={percent(kpis.attendance_percentage ?? kpis.attendance)} />
        <StatCard label="Average result" value={percent(kpis.average_score ?? kpis.results_average)} />
        <StatCard label="Open remediation" value={counts.OPEN ?? "—"} to="/admin/analytics/tasks" />
      </div>

      <h2 style={{ marginTop: "1.5rem" }}>Cohorts</h2>
      <DataTable
        columns={[
          { key: "class_name", label: "Class", render: (r) => r.class_name || r.class || "—" },
          { key: "subject", label: "Subject", render: (r) => r.subject || "—" },
          { key: "learner_count", label: "Learners", render: (r) => r.learner_count ?? r.count ?? "—" },
          { key: "mastery_percentage", label: "Mastery", render: (r) => percent(r.mastery_percentage ?? r.average_mastery) },
          { key: "attendance_percentage", label: "Attendance", render: (r) => percent(r.attendance_percentage) },
          { key: "result_average", label: "Results", render: (r) => percent(r.result_average ?? r.results_average) },
        ]}
        rows={rows}
        loading={false}
        error={null}
        emptyTitle="No cohort data yet"
        emptyHint="Cohorts are built from learners, attendance and assessment records."
      />
    </section>
  );
}
