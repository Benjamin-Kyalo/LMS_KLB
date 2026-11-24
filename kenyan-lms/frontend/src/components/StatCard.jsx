import { Link } from "react-router-dom";

export default function StatCard({ value, label, to, hint }) {
  const inner = (
    <>
      <div className="num">{value ?? "—"}</div>
      <div className="label">{label}</div>
      {hint && <div className="stat-hint">{hint}</div>}
    </>
  );
  if (to) {
    return (
      <Link className="stat stat-link" to={to} aria-label={`${label}: ${value ?? "none"}. Open details`}>
        {inner}
      </Link>
    );
  }
  return <div className="stat">{inner}</div>;
}
