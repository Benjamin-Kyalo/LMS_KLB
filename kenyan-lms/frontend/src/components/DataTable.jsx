import Loading from "./Loading";
import EmptyState from "./EmptyState";

export default function DataTable({ columns, rows, loading, error, emptyTitle = "Nothing here yet", emptyHint, emptyAction }) {
  if (loading) return <Loading />;
  if (error) return <div className="notice error" role="alert">{error}</div>;
  if (!rows || rows.length === 0) return <EmptyState title={emptyTitle} hint={emptyHint} action={emptyAction} />;
  return (
    <div className="panel" style={{ overflowX: "auto" }}>
      <table className="data">
        <thead>
          <tr>{columns.map((c) => <th key={c.key} scope="col">{c.label}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={row.id ?? row.reference ?? index}>
              {columns.map((c) => (
                <td key={c.key}>{c.render ? c.render(row) : (row[c.key] ?? "—")}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
