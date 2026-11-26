import { useState } from "react";
import { useList } from "../hooks/useApi";
import useTableControls from "../hooks/useTableControls";
import DataTable from "../components/DataTable";
import Modal from "../components/Modal";
import RollingLabel from "../components/RollingLabel";
import { TableToolbar, TablePagination } from "../components/TableTools";
import { formatDateTime } from "../utilities/format";

function readable(value) {
  if (value === null || value === undefined || value === "") return "—";
  if (Array.isArray(value)) return value.map(readable).join(", ");
  if (typeof value === "object") {
    return Object.entries(value)
      .map(([key, item]) => `${readable(key)}: ${readable(item)}`)
      .join(" · ");
  }
  return String(value).replaceAll("_", " ");
}

function actionTag(action) {
  const className = action.endsWith(".created") || action.endsWith(".verified")
    ? "good"
    : action.includes("rejected") || action.includes("failed")
      ? "bad"
      : "info";
  return <span className={`tag ${className}`}>{readable(action)}</span>;
}

export default function AuditHistory() {
  const history = useList("/core/audit/");
  const controls = useTableControls(history.data);
  const [action, setAction] = useState("");
  const [entityType, setEntityType] = useState("");
  const [selected, setSelected] = useState(null);

  const actions = [...new Set((history.data || []).map((row) => row.action))].sort();
  const entityTypes = [...new Set((history.data || []).map((row) => row.entity_type))].sort();
  const rows = controls.filteredRows.filter((row) =>
    (!action || row.action === action) && (!entityType || row.entity_type === entityType)
  );

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">Accountability</div>
          <h1>Audit history</h1>
          <p className="muted">
            A read-only trail of who changed a record, when, and which fields changed.
          </p>
        </div>
        <div className="actions">
          <button className="secondary" onClick={history.reload} aria-busy={history.loading || undefined}>
            {history.loading ? "Refreshing…" : <RollingLabel>Refresh history</RollingLabel>}
          </button>
        </div>
      </div>

      {history.error && <div className="notice error" role="alert">{history.error}</div>}

      <div className="notice info">
        Audit entries cannot be edited or deleted here. Sensitive fields such as passwords are
        never included in a change record.
      </div>

      <TableToolbar
        title="audit entries"
        controls={controls}
        onRefresh={history.reload}
        extra={
          <>
            <label className="inline-filter">
              Action
              <select value={action} onChange={(event) => setAction(event.target.value)}>
                <option value="">All actions</option>
                {actions.map((item) => <option key={item} value={item}>{readable(item)}</option>)}
              </select>
            </label>
            <label className="inline-filter">
              Record type
              <select value={entityType} onChange={(event) => setEntityType(event.target.value)}>
                <option value="">All record types</option>
                {entityTypes.map((item) => <option key={item} value={item}>{readable(item)}</option>)}
              </select>
            </label>
          </>
        }
      />

      <DataTable
        columns={[
          {
            key: "actor_name",
            label: "Changed by",
            render: (row) => row.actor_name || row.actor_username || "System",
          },
          { key: "action", label: "Action", render: (row) => actionTag(row.action) },
          {
            key: "entity",
            label: "Record",
            render: (row) => `${readable(row.entity_type)} #${row.entity_id ?? "—"}`,
          },
          { key: "created_at", label: "When", render: (row) => formatDateTime(row.created_at) },
          {
            key: "changed_fields",
            label: "Fields",
            render: (row) => (row.details?.changed_fields || []).join(", ") || "—",
          },
          {
            key: "actions",
            label: "Actions",
            render: (row) => (
              <button
                type="button"
                className="ghost small"
                aria-label={`View audit entry ${row.id}`}
                onClick={() => setSelected(row)}
              >
                <RollingLabel>View details</RollingLabel>
              </button>
            ),
          },
        ]}
        rows={rows}
        loading={history.loading}
        error={history.error}
        emptyTitle={controls.query || action || entityType ? "No matching entries" : "No changes recorded yet"}
        emptyHint="Edits and workflow decisions appear here as soon as they are saved."
      />
      <TablePagination controls={controls} />

      {selected && (
        <Modal title={`Audit entry #${selected.id}`} onClose={() => setSelected(null)}>
          <dl className="detail-list">
            <div><dt>Changed by</dt><dd>{selected.actor_name || selected.actor_username || "System"}</dd></div>
            <div><dt>Action</dt><dd>{readable(selected.action)}</dd></div>
            <div><dt>Record</dt><dd>{readable(selected.entity_type)} #{selected.entity_id ?? "—"}</dd></div>
            <div><dt>When</dt><dd>{formatDateTime(selected.created_at)}</dd></div>
            <div><dt>IP address</dt><dd>{selected.ip_address || "—"}</dd></div>
          </dl>

          {selected.details?.changed_fields?.length ? (
            <>
              <h3>Field changes</h3>
              <div className="panel" style={{ overflowX: "auto" }}>
                <table className="data">
                  <thead>
                    <tr>
                      <th scope="col">Field</th>
                      <th scope="col">Before</th>
                      <th scope="col">After</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selected.details.changed_fields.map((field) => (
                      <tr key={field}>
                        <td className="mono">{field}</td>
                        <td>{readable(selected.details.before?.[field])}</td>
                        <td>{readable(selected.details.after?.[field])}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <>
              <h3>Details</h3>
              <ul>
                {Object.entries(selected.details || {}).map(([key, value]) => (
                  <li key={key}><strong>{readable(key)}:</strong> {readable(value)}</li>
                ))}
              </ul>
            </>
          )}

          <div className="form-actions">
            <button type="button" className="ghost" onClick={() => setSelected(null)}>
              <RollingLabel>Close</RollingLabel>
            </button>
          </div>
        </Modal>
      )}
    </section>
  );
}
