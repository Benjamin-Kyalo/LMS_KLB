export default function EmptyState({ title, hint, action }) {
  return (
    <div className="panel panel-pad" style={{ textAlign: "center", padding: "2rem" }}>
      <h3>{title}</h3>
      <p className="muted">{hint}</p>
      {action}
    </div>
  );
}
