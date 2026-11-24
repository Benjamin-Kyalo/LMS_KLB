import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useList } from "../hooks/useApi";
import { api } from "../services/api";
import ChartCard from "../components/ChartCard";
import Loading from "../components/Loading";

const STATUS_COLORS = {
  PRESENT: "#0B3D2E",
  ABSENT: "#B44635",
  LATE: "#8A5A15",
  EXCUSED: "#1C5D7E",
};

export default function Reports() {
  const { data: learners, loading } = useList("/reports/my-learners/");
  const [params] = useSearchParams();
  const [selected, setSelected] = useState("");
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  const load = useCallback(async (id) => {
    setSelected(String(id));
    setError(null);
    setReport(null);
    if (!id) return;
    try { setReport(await api.get(`/reports/learner/${id}/`)); }
    catch (err) { setError(err.message); }
  }, []);

  useEffect(() => {
    if (loading || !learners?.length || selected) return;
    const requested = params.get("learner");
    const match = learners.find((item) => String(item.id) === requested);
    load(match ? match.id : learners[0].id);
  }, [loading, learners, selected, params, load]);

  const attendanceData = Object.entries(report?.attendance || {}).map(([status, value]) => ({
    status,
    label: status.charAt(0) + status.slice(1).toLowerCase(),
    value,
    fill: STATUS_COLORS[status],
  }));
  const examData = (report?.exams || []).map((item) => {
    const name = item.label || item.exam || "Exam";
    return {
      label: name.length > 18 ? `${name.slice(0, 17)}…` : name,
      percentage: item.percentage,
    };
  });

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">Reporting</div>
          <h1>Learner report</h1>
        </div>
      </div>

      {loading ? <Loading /> : (
        <div className="panel panel-pad" style={{ marginBottom: "1rem", maxWidth: 420 }}>
          <label htmlFor="learner">Choose a learner</label>
          <select id="learner" value={selected} onChange={(e) => load(e.target.value)}>
            <option value="">— choose —</option>
            {(learners || []).map((item) => (
              <option key={item.id} value={item.id}>
                {item.learner_name} ({item.admission_number})
              </option>
            ))}
          </select>
          {!learners?.length && <p className="muted">No learner reports are available for this account.</p>}
        </div>
      )}

      {error && <div className="notice error">{error}</div>}

      {report && (
        <div>
          <div className="panel panel-pad" style={{ marginBottom: "1rem" }}>
            <h2>{report.learner.name}</h2>
            <p className="muted">{report.learner.admission_number} · {report.learner.class || "No class"} · {report.learner.institution}</p>
            <p><strong>Average score:</strong> {report.average_score ?? "—"}</p>
            {report.permissions?.academics === false && (
              <p className="muted">Academic results are hidden by this learner's guardian permissions.</p>
            )}
          </div>

          <div className="chart-grid">
            <ChartCard
              title="Attendance"
              subtitle="Recorded days by status"
              type="pie"
              data={attendanceData}
              emptyText="No attendance recorded."
            />
            <ChartCard
              title="Exam scores"
              subtitle="Percentage score by exam"
              type="bar"
              data={examData}
              xKey="label"
              series={[{ key: "percentage", label: "Score %", colour: "#1C5D7E" }]}
              emptyText="No exam results recorded yet."
            />
          </div>

          <div className="panel panel-pad" style={{ marginTop: "1rem" }}>
            <h3>Exam detail</h3>
            {!report.exams?.length ? <p className="muted">No exam results yet.</p> : (
              <div style={{ overflowX: "auto" }}>
                <table className="data">
                  <thead><tr><th>Exam</th><th>Date</th><th>Score</th><th>Grade</th></tr></thead>
                  <tbody>
                    {report.exams.map((item, index) => (
                      <tr key={index}>
                        <td>{item.label || item.exam || "—"}</td>
                        <td>{item.date || "—"}</td>
                        <td>{item.score}{item.max_score != null ? ` / ${item.max_score}` : ""}</td>
                        <td>{item.grade || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
