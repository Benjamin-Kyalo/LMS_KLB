export default function EmptyState({ title, hint, action, headingLevel = 3 }) {
  const Heading = `h${headingLevel}`;
  return (
    <div className="panel panel-pad" style={{ textAlign: "center", padding: "2rem" }}>
      <Heading>{title}</Heading>
      <p className="muted">{hint}</p>
      {action}
    </div>
  );
}
