import { useResource } from "../hooks/useApi";
import Loading from "../components/Loading";
import StatCard from "../components/StatCard";
import { formatDate } from "../utilities/format";

const LEVEL_LABELS = {
  BEGINNING: "Beginning",
  DEVELOPING: "Developing",
  ACHIEVING: "Achieving",
  EXTENDING: "Extending",
};

export default function PortalMastery() {
  const report = useResource("/analytics/my-mastery/");

  if (report.loading) return <Loading label="Loading your badges…" />;
  const summary = report.data?.summary || {};
  const badges = report.data?.badges || [];

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">My progress</div>
          <h1>My mastery badges</h1>
          <p className="muted">A clear view of the competency evidence your teachers have recorded.</p>
        </div>
      </div>

      {report.error && <div className="notice error" role="alert">{report.error}</div>}

      <div className="notice">
        These badges are displays of recorded evidence, not awarded certificates. Achieving and
        extending bands count as earned; beginning and developing bands show progress.
      </div>

      <div className="stat-grid" style={{ marginTop: "1rem" }}>
        <StatCard label="Badge displays" value={summary.badges ?? 0} />
        <StatCard label="Earned" value={summary.earned_badges ?? 0} />
      </div>

      <div className="panel panel-pad" style={{ marginTop: "1.25rem" }}>
        <h2 style={{ marginTop: 0 }}>My badges</h2>
        {badges.length === 0 ? (
          <p className="muted">No competency evidence has been recorded for you yet.</p>
        ) : (
          <div className="stack">
            {badges.map((badge) => (
              <article key={`${badge.competency_id}-${badge.mastery_level}`} className={`notice ${badge.earned ? "success" : ""}`}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: "0.75rem", flexWrap: "wrap" }}>
                  <strong>{badge.competency_name}</strong>
                  <span className={`tag ${badge.earned ? "good" : "info"}`}>
                    {badge.earned ? "Earned" : "In progress"}
                  </span>
                </div>
                <p className="muted" style={{ margin: "0.4rem 0" }}>
                  Band: {LEVEL_LABELS[badge.mastery_level] || badge.mastery_level} · average {badge.score_percent}%
                  from {badge.evidence_count} evidence row{badge.evidence_count === 1 ? "" : "s"}.
                </p>
                <p className="muted" style={{ margin: 0 }}>
                  Latest evidence: {formatDate(badge.recent_evidence_at)}.
                </p>
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
