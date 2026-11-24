import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useResource } from "../hooks/useApi";
import StatCard from "../components/StatCard";
import ChartCard from "../components/ChartCard";
import Loading from "../components/Loading";
import { isAdmin, isLearner, isGuardian, isTeacher } from "../utilities/roles";

const STATUS_COLORS = {
  PRESENT: "#0B3D2E",
  ABSENT: "#B44635",
  LATE: "#8A5A15",
  EXCUSED: "#1C5D7E",
};

export default function Dashboard() {
  const { user } = useAuth();
  const staffView = !(isLearner(user) || isGuardian(user));
  const quickBase = staffView ? "/admin" : "/portal";
  const summary = useResource(staffView ? "/reports/dashboard/" : null);
  const charts = useResource(staffView ? "/reports/analytics/" : null);

  if (!user) return <Loading />;
  if (staffView && (summary.loading || charts.loading)) return <Loading />;

  const chartData = charts.data || {};
  const trend = (chartData.attendance_trend || []).map((item) => ({
    label: item.date.slice(5),
    PRESENT: item.PRESENT,
    ABSENT: item.ABSENT,
    LATE: item.LATE,
    EXCUSED: item.EXCUSED,
  }));
  const exams = (chartData.exam_results || []).map((item) => ({
    label: item.label.length > 18 ? `${item.label.slice(0, 17)}…` : item.label,
    percentage: item.percentage,
  }));
  const attendanceStatus = (chartData.attendance_status || []).map((item) => ({
    ...item,
    fill: STATUS_COLORS[item.status],
  }));

  function refresh() {
    summary.reload();
    charts.reload();
  }

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">Overview</div>
          <h1>Karibu, {user.first_name || user.username}</h1>
        </div>
        <div className="actions">
          {staffView && <button className="secondary" onClick={refresh}>Refresh data</button>}
        </div>
      </div>

      {staffView && (summary.error || charts.error) ? (
        <div className="notice error" style={{ marginBottom: "1rem" }}>
          {summary.error || charts.error}{" "}
          <button className="ghost small" onClick={refresh}>Try again</button>
        </div>
      ) : null}

      {staffView && !summary.error && (
        <>
          <div className="stat-grid">
            <StatCard value={summary.data?.total_learners} label="Learners" to="/admin/learners" hint="Open learner records" />
            <StatCard value={summary.data?.active_learners} label="Active learners" to="/admin/learners" hint="Open learner records" />
            <StatCard
              value={summary.data?.attendance_rate_percent != null ? `${summary.data.attendance_rate_percent}%` : "—"}
              label="Attendance rate"
              to="/admin/attendance"
              hint="Open attendance register"
            />
            <StatCard
              value={summary.data?.average_exam_score ?? "—"}
              label="Average exam score"
              to="/admin/exams"
              hint="Open exams and results"
            />
          </div>

          <div className="chart-grid">
            <ChartCard
              title="Attendance mix"
              subtitle="Present, absent, late and excused"
              type="pie"
              data={attendanceStatus}
              emptyText="No attendance records yet."
            />
            <ChartCard
              title="Attendance over time"
              subtitle="Last 14 recorded days"
              type="line"
              data={trend}
              xKey="label"
              series={[
                { key: "PRESENT", label: "Present", colour: "#0B3D2E" },
                { key: "ABSENT", label: "Absent", colour: "#B44635" },
                { key: "LATE", label: "Late", colour: "#8A5A15" },
                { key: "EXCUSED", label: "Excused", colour: "#1C5D7E" },
              ]}
              emptyText="Attendance dates will appear here once marked."
            />
            <ChartCard
              title="Exam performance"
              subtitle="Percentage score by exam"
              type="bar"
              data={exams}
              xKey="label"
              series={[{ key: "percentage", label: "Score %", colour: "#1C5D7E" }]}
              emptyText="No exam results recorded yet."
            />
            <ChartCard
              title="Learner status"
              subtitle="Active, transferred, alumni and suspended"
              type="pie"
              data={chartData.learner_status || []}
              emptyText="No learners registered yet."
            />
          </div>
        </>
      )}

      <div className="panel panel-pad" style={{ marginTop: "1.25rem" }}>
        <h2>Where to next?</h2>
        <div className="quick-links">
          {(isAdmin(user) || isTeacher(user)) && <Link to="/admin/learners">Manage learners →</Link>}
          {(isAdmin(user) || isTeacher(user)) && <Link to="/admin/attendance">Mark attendance →</Link>}
          {(isAdmin(user) || isTeacher(user)) && <Link to="/admin/courses">Courses and lessons →</Link>}
          <Link to={`${quickBase}/textbooks`}>Digital textbooks →</Link>
          <Link to={`${quickBase}/assignments`}>Assignments →</Link>
          <Link to={`${quickBase}/reports`}>Reports →</Link>
          {isGuardian(user) && <Link to="/portal/reports">Your child's progress →</Link>}
          {isLearner(user) && <Link to="/portal/courses">Continue learning →</Link>}
        </div>
      </div>

      {isAdmin(user) && (
        <div className="panel panel-pad" style={{ marginTop: "1rem" }}>
          <h2>Administrator actions</h2>
          <div className="quick-links">
            <Link to="/admin/learners">Register a learner</Link>
            <Link to="/admin/teachers">Add a teacher</Link>
            <Link to="/admin/guardians">Link a guardian</Link>
            <Link to="/admin/classes">Set up subjects</Link>
            <Link to="/admin/school">Update school profile</Link>
            <Link to="/admin/institutions">Manage institutions</Link>
            <Link to="/admin/communications">Publish an announcement</Link>
          </div>
        </div>
      )}
    </section>
  );
}
