import { useState } from "react";
import { useResource } from "../hooks/useApi";
import useTableControls from "../hooks/useTableControls";
import DataTable from "../components/DataTable";
import Loading from "../components/Loading";
import StatCard from "../components/StatCard";
import { TablePagination, TableToolbar } from "../components/TableTools";
import { formatDate } from "../utilities/format";

const LEVEL_LABELS = {
  BEGINNING: "Beginning",
  DEVELOPING: "Developing",
  ACHIEVING: "Achieving",
  EXTENDING: "Extending",
};

function levelTag(level) {
  const className = level === "EXTENDING" || level === "ACHIEVING"
    ? "good" : level === "DEVELOPING" ? "warn" : "info";
  return <span className={`tag ${className}`}>{LEVEL_LABELS[level] || level || "—"}</span>;
}

export default function MasteryBadges() {
  const report = useResource("/analytics/mastery/");
  const controls = useTableControls(report.data?.badges || []);
  const [level, setLevel] = useState("");

  if (report.loading) return <Loading label="Loading mastery badges…" />;
  const summary = report.data?.summary || {};
  const badges = report.data?.badges || [];
  const bands = report.data?.rules?.badge_bands || [];
  const rows = level
    ? controls.filteredRows.filter((row) => row.mastery_level === level)
    : controls.filteredRows;

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">Competency evidence</div>
          <h1>Mastery badges</h1>
          <p className="muted">Derived displays from recorded competency evidence. Nothing here is awarded automatically.</p>
        </div>
      </div>

      {report.error && <div className="notice error" role="alert">{report.error}</div>}

      <div className="stat-grid">
        <StatCard label="Learners with evidence" value={summary.learners ?? "—"} />
        <StatCard label="Badge displays" value={summary.badges ?? "—"} />
        <StatCard label="Earned (achieving or above)" value={summary.earned_badges ?? "—"} />
      </div>

      <div className="panel panel-pad" style={{ marginTop: "1.25rem" }}>
        <h2 style={{ marginTop: 0 }}>How bands are calculated</h2>
        <ul>
          {bands.map((band) => (
            <li key={band.code}>
              <strong>{LEVEL_LABELS[band.code] || band.code}</strong> — from {Number(band.min_score) * 100}%
              {band.earned ? " · earned badge" : " · progress band"}
            </li>
          ))}
        </ul>
        <p className="muted">
          Each learner's scores are averaged per competency from existing evidence rows. A badge
          display is not a credential and does not create an award record.
        </p>
      </div>

      <h2 style={{ marginTop: "1.5rem" }}>Learner badge displays</h2>
      <TableToolbar
        title="badges"
        controls={controls}
        onRefresh={report.reload}
        extra={
          <label className="inline-filter">
            Band
            <select value={level} onChange={(event) => setLevel(event.target.value)}>
              <option value="">All</option>
              {bands.map((band) => (
                <option key={band.code} value={band.code}>{LEVEL_LABELS[band.code] || band.code}</option>
              ))}
            </select>
          </label>
        }
      />
      <DataTable
        columns={[
          { key: "learner_name", label: "Learner" },
          { key: "admission_number", label: "Admission no." },
          { key: "competency_name", label: "Competency" },
          { key: "mastery_level", label: "Band", render: (row) => levelTag(row.mastery_level) },
          { key: "score_percent", label: "Average", render: (row) => `${row.score_percent}%` },
          { key: "evidence_count", label: "Evidence rows" },
          { key: "recent_evidence_at", label: "Latest", render: (row) => formatDate(row.recent_evidence_at) },
          {
            key: "earned",
            label: "Status",
            render: (row) => <span className={`tag ${row.earned ? "good" : "info"}`}>{row.earned ? "Earned" : "In progress"}</span>,
          },
        ]}
        rows={rows}
        loading={false}
        error={null}
        emptyTitle={level ? `No ${LEVEL_LABELS[level]?.toLowerCase() || level.toLowerCase()} badges` : "No competency evidence yet"}
        emptyHint="Record competency evidence for a learner to see a derived badge display."
      />
      <TablePagination controls={controls} />

      {badges.length === 0 && !report.error && (
        <p className="muted">Badge displays appear when staff record competency evidence against a competency.</p>
      )}
    </section>
  );
}
