export default function Loading({ label = "Loading…" }) {
  return <p className="muted" role="status">{label}</p>;
}
