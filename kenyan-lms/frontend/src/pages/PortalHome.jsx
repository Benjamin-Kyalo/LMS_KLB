import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useList } from "../hooks/useApi";
import { api } from "../services/api";
import ChartCard from "../components/ChartCard";
import Loading from "../components/Loading";
import { isGuardian, isLearner } from "../utilities/roles";
import { useTheme } from "../context/ThemeContext";
import { useSiteContent } from "../context/SiteContentContext";

export default function PortalHome() {
  const { user } = useAuth();
  const { colors } = useTheme();
  const { content } = useSiteContent();
  const messages = content.messages || {};
  const reportsIntro = messages.pageIntroductions?.reports
    || "Explore the available records and reports to understand activity and progress.";
  const reportLoading = messages.loading?.[5] || "Preparing your report...";
  const somethingWrong = messages.errors?.somethingWrong
    || "We could not complete that action. Try again, or contact support if the problem continues. Include the reference number shown on this page.";
  const { data: learners, loading } = useList("/reports/my-learners/");
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (loading || !learners.length || report) return;
    api.get(`/reports/learner/${learners[0].id}/`)
      .then(setReport)
      .catch((err) => setError(err.message || somethingWrong));
  }, [loading, learners, report]);

  if (!isLearner(user) && !isGuardian(user)) return <Navigate to="/admin" replace />;
  if (loading) return <Loading label={reportLoading} />;

  const guardian = isGuardian(user);
  const attendanceData = Object.entries(report?.attendance || {}).map(([status, value]) => ({
    status,
    label: status.charAt(0) + status.slice(1).toLowerCase(),
    value,
    fill: colors.attendance[status],
  }));
  const examData = (report?.exams || []).map((item) => {
    const label = item.label || item.exam || "Exam";
    return {
      label: label.length > 18 ? `${label.slice(0, 17)}…` : label,
      percentage: item.percentage,
    };
  });

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">{guardian ? "Family" : "Your learning"}</div>
          <h1>Habari, {user.first_name || user.username}</h1>
          <p className="muted" style={{ marginTop: "0.2rem" }}>{reportsIntro}</p>
        </div>
      </div>

      {error && <div className="notice error" role="alert">{error}</div>}

      {!learners.length ? (
        <div className="panel panel-pad" style={{ textAlign: "center", padding: "2rem" }}>
          <h3>No linked learner yet</h3>
          <p className="muted">
            {guardian
              ? "Submit your learner's admission number in first-time setup. Reports open after your school verifies the link."
              : "Your school administrator must add a learner record for you before reports can be shown."}
          </p>
          {guardian && user?.onboarding?.is_complete === false && (
            <p style={{ marginTop: "0.8rem" }}><Link to="/onboarding">Complete setup →</Link></p>
          )}
        </div>
      ) : (
        <>
          <div className="panel panel-pad" style={{ marginBottom: "1rem" }}>
            <div className="overline">{guardian ? "Linked learner" : "Your record"}</div>
            <h2>{report?.learner?.name || learners[0].learner_name}</h2>
            <p className="muted">
              {report?.learner?.admission_number || learners[0].admission_number}
              {" · "}{report?.learner?.class || "No class"} · {report?.learner?.institution || user.institution_name}
            </p>
            <div className="stat-grid" style={{ marginBottom: 0, marginTop: "0.8rem" }}>
              <div className="stat">
                <div className="num">{report?.average_score ?? "—"}</div>
                <div className="label">Average score</div>
              </div>
              <div className="stat secondary">
                <div className="num">
                  {attendanceData.find((item) => item.status === "PRESENT")?.value ?? "—"}
                </div>
                <div className="label">Days present</div>
              </div>
            </div>
          </div>

          <div className="chart-grid">
            <ChartCard
              title="Attendance"
              subtitle="Recorded days by status"
              type="pie"
              data={attendanceData}
              emptyText="No attendance recorded yet."
            />
            <ChartCard
              title="Assessment scores"
              subtitle="Percentage score by exam"
              type="bar"
              data={examData}
              xKey="label"
              series={[{ key: "percentage", label: "Score %", colour: colors.score }]}
              emptyText="No exam results recorded yet."
            />
          </div>
        </>
      )}

      <div className="panel panel-pad">
        <h2>Continue</h2>
        <div className="quick-links">
          <Link to="/portal/courses">Open my courses →</Link>
          <Link to="/portal/textbooks">Read a textbook →</Link>
          <Link to="/portal/assignments">View assignments →</Link>
          <Link to="/portal/reports">Full progress report →</Link>
          <Link to="/portal/communications">School messages →</Link>
        </div>
      </div>
    </section>
  );
}
