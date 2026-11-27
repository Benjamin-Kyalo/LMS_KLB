import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useResource } from "../hooks/useApi";
import StatCard from "../components/StatCard";
import ChartCard from "../components/ChartCard";
import Loading from "../components/Loading";
import RollingLabel from "../components/RollingLabel";
import { isAdmin, isLearner, isGuardian, isTeacher } from "../utilities/roles";
import { useTheme } from "../context/ThemeContext";
import { useSiteContent } from "../context/SiteContentContext";

function stepsFor(user) {
  if (isLearner(user)) {
    return [
      { title: "Continue learning", to: "/portal/courses", hint: "Pick up where you left off." },
      { title: "Complete assignments", to: "/portal/assignments", hint: "See what is due soon." },
      { title: "Read your books", to: "/portal/textbooks", hint: "Open your digital library." },
    ];
  }
  if (isGuardian(user)) {
    return [
      { title: "Check progress", to: "/portal/reports", hint: "Review your learner's latest results." },
      { title: "Read messages", to: "/portal/communications", hint: "Stay up to date with school notices." },
      { title: "Explore resources", to: "/portal/resources", hint: "Find learning support materials." },
    ];
  }
  const steps = [];
  if (isAdmin(user)) {
    steps.push(
      { title: "Review teacher approvals", to: "/admin/teacher-approvals", hint: "Approve new staff accounts." },
      { title: "Verify guardian links", to: "/admin/guardian-links", hint: "Confirm family connections." },
    );
  }
  steps.push(
    { title: "Check attendance", to: "/admin/attendance", hint: "Follow up on gaps and patterns." },
    { title: "Plan learning", to: "/admin/courses", hint: "Keep courses and lessons current." },
    { title: "Open full analytics", to: "/admin/analytics", hint: "See trends across attendance and results." }
  );
  return steps.slice(0, 4);
}

export default function Dashboard() {
  const { user } = useAuth();
  const { colors } = useTheme();
  const { content } = useSiteContent();
  const messages = content.messages || {};
  const overview = messages.pageIntroductions?.overview
    || "Here is a summary of the activities and information available to your account.";
  const dashboardLoading = messages.loading?.[0] || "Preparing your dashboard...";
  const somethingWrong = messages.errors?.somethingWrong
    || "We could not complete that action. Try again, or contact support if the problem continues. Include the reference number shown on this page.";
  const staffView = !(isLearner(user) || isGuardian(user));
  const summary = useResource(staffView ? "/reports/dashboard/" : null);
  const charts = useResource(staffView ? "/reports/analytics/" : null);

  if (!user) return <Loading label={messages.loading?.[6] || "Checking your account..."} />;
  if (staffView && (summary.loading || charts.loading)) return <Loading label={dashboardLoading} />;

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
  const steps = stepsFor(user);

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
          <p>{overview}</p>
        </div>
        <div className="actions">
          {staffView && (
            <button className="secondary" onClick={refresh}>
              <RollingLabel>Refresh data</RollingLabel>
            </button>
          )}
        </div>
      </div>

      {staffView && (summary.error || charts.error) ? (
        <div className="notice error" role="alert" style={{ marginBottom: "1rem" }}>
          {somethingWrong}{" "}
          <button className="ghost small" onClick={refresh}><RollingLabel>Try again</RollingLabel></button>
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

          <div className="chart-grid chart-grid--focused">
            <ChartCard
              title="Attendance over time"
              subtitle="Last 14 recorded days"
              type="line"
              data={trend}
              xKey="label"
              series={[
                { key: "PRESENT", label: "Present", colour: colors.attendance.PRESENT },
                { key: "ABSENT", label: "Absent", colour: colors.attendance.ABSENT },
                { key: "LATE", label: "Late", colour: colors.attendance.LATE },
                { key: "EXCUSED", label: "Excused", colour: colors.attendance.EXCUSED },
              ]}
              emptyText="Attendance dates will appear here once marked."
            />
            <ChartCard
              title="Exam performance"
              subtitle="Percentage score by exam"
              type="bar"
              data={exams}
              xKey="label"
              series={[{ key: "percentage", label: "Score %", colour: colors.score }]}
              emptyText="No exam results recorded yet."
            />
          </div>
          <div className="chart-more">
            <Link to="/admin/analytics">Open the full analytics view →</Link>
          </div>
        </>
      )}

      <div className="panel panel-pad roadmap" style={{ marginTop: "1.25rem" }}>
        <div className="roadmap-heading">
          <div className="overline">Guided path</div>
          <h2>Start here</h2>
          <p>A short, role-aware path through the most useful next actions.</p>
        </div>
        <ol className="roadmap-steps">
          {steps.map((step, index) => (
            <li key={step.to + step.title}>
              <span className="roadmap-step-number" aria-hidden="true">{index + 1}</span>
              <div className="roadmap-step-copy">
                <strong>{step.title}</strong>
                <p>{step.hint}</p>
              </div>
              <Link to={step.to} className="button-link roadmap-step-link" aria-label={`Open ${step.title}`}>
                <RollingLabel>Open {step.title}</RollingLabel>{" "}
                <span className="arrow" aria-hidden="true">→</span>
              </Link>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
