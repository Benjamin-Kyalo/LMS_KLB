import { useState } from "react";
import { useList } from "../hooks/useApi";
import DataTable from "./DataTable";
import Modal from "./Modal";

function display(value) {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

// Read-only list used by the learner/guardian portal. It deliberately has no
// create, edit or delete controls: those belong to the staff admin panel.
export default function PortalList({ title, overline, endpoint, columns, emptyHint }) {
  const { data, loading, error, reload } = useList(endpoint);
  const [detail, setDetail] = useState(null);

  const allColumns = [
    ...columns,
    {
      key: "_actions",
      label: "",
      render: (row) => <button className="ghost small" onClick={() => setDetail(row)}>View</button>,
    },
  ];

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">{overline}</div>
          <h1>{title}</h1>
        </div>
        <div className="actions"><button className="secondary" onClick={reload}>Refresh</button></div>
      </div>

      <DataTable
        columns={allColumns}
        rows={data}
        loading={loading}
        error={error}
        emptyTitle={`No ${title.toLowerCase()} available yet`}
        emptyHint={emptyHint}
      />

      {detail && (
        <Modal title={`${title} details`} onClose={() => setDetail(null)}>
          <dl className="detail-list">
            {columns.map((column) => (
              <div key={column.key}>
                <dt>{column.label}</dt>
                <dd>{display(detail[column.key])}</dd>
              </div>
            ))}
          </dl>
          <div className="form-actions">
            <button type="button" className="ghost" onClick={() => setDetail(null)}>Close</button>
          </div>
        </Modal>
      )}
    </section>
  );
}
