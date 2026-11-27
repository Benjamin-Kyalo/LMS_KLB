import { useState } from "react";
import { useLowBandwidth } from "../context/LowBandwidthContext";
import { useToast } from "../context/ToastContext";
import DataTable from "../components/DataTable";
import RollingLabel from "../components/RollingLabel";
import StatCard from "../components/StatCard";
import {
  clearCache, clearConflicts, dismissConflict, listConflicts, listOutbox,
} from "../services/lowBandwidth";
import { formatDateTime } from "../utilities/format";

export default function LowBandwidth() {
  const { config, online, revision, status, flush } = useLowBandwidth();
  const { push } = useToast();
  const [busy, setBusy] = useState(false);
  const offline = config?.offline;
  const enabled = Boolean(offline?.enabled);
  const queued = listOutbox();
  const conflicts = listConflicts();
  // revision is read so storage changes made outside this page trigger a render.
  void revision;

  async function retry() {
    setBusy(true);
    try {
      const result = await flush();
      push(
        `Retried ${queued.length} queued change(s): ${result.sent} saved, ${result.conflicts} need review.`,
        result.conflicts ? "warn" : "success",
      );
    } catch (error) {
      push(error.message || "The queued changes could not be retried.", "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">Connectivity</div>
          <h1>Low-bandwidth status</h1>
          <p className="muted">See what is cached on this device and retry changes saved during a weak connection.</p>
        </div>
        <div className="actions">
          <button
            aria-busy={busy || undefined}
            disabled={busy || !enabled || !online || queued.length === 0}
            onClick={retry}
          >
            {busy ? "Retrying…" : <RollingLabel>Retry queued changes</RollingLabel>}
          </button>
        </div>
      </div>

      <div className="notice" role="status">
        <strong>Connection: {online ? "online" : "offline"}.</strong>{" "}
        {enabled
          ? "Low-bandwidth mode is enabled. The first page load still needs a network connection; no service worker or installed app is used."
          : "Low-bandwidth mode is not enabled by the server. Failed changes stay unsaved unless an operator turns this on."}
      </div>

      <div className="stat-grid" style={{ marginTop: "1rem" }}>
        <StatCard label="Cached public reads" value={status.cached_reads} />
        <StatCard label="Queued changes" value={status.queued_writes} />
        <StatCard label="Needs review" value={status.conflicts} />
      </div>

      <div className="panel panel-pad" style={{ marginTop: "1.25rem" }}>
        <h2 style={{ marginTop: 0 }}>Privacy limits</h2>
        <ul>
          <li>Only public pages named by the server are cached.</li>
          <li>Session cookies, CSRF tokens and credentials are never saved.</li>
          <li>Changes with person-like or credential-like fields are refused before they are queued.</li>
          <li>No badge display, fee record or learner document is stored on the device by this feature.</li>
        </ul>
      </div>

      <h2 style={{ marginTop: "1.5rem" }}>Queued changes</h2>
      <DataTable
        columns={[
          { key: "method", label: "Action" },
          { key: "path", label: "Endpoint" },
          { key: "created_at", label: "Queued at", render: (row) => formatDateTime(row.created_at) },
          { key: "if_match", label: "Version", render: (row) => (row.if_match ? "Attached" : "Not attached") },
        ]}
        rows={queued}
        loading={false}
        error={null}
        emptyTitle="Nothing queued"
        emptyHint="Failed changes appear here only when the server allows this endpoint to be queued."
      />

      <h2 style={{ marginTop: "1.5rem" }}>Changes needing review</h2>
      <DataTable
        columns={[
          { key: "method", label: "Action" },
          { key: "path", label: "Endpoint" },
          { key: "message", label: "Reason" },
          { key: "server_updated_at", label: "Server version", render: (row) => formatDateTime(row.server_updated_at) },
          {
            key: "actions",
            label: "Actions",
            render: (row) => (
              <button
                type="button"
                className="ghost small"
                aria-label={`Dismiss conflict for ${row.method} ${row.path}`}
                onClick={() => { dismissConflict(row.id); push("Conflict dismissed.", "success"); }}
              >
                <RollingLabel>Dismiss</RollingLabel>
              </button>
            ),
          },
        ]}
        rows={conflicts}
        loading={false}
        error={null}
        emptyTitle="No conflicts"
        emptyHint="If a queued change meets a newer server version, it is shown here instead of overwriting work."
      />

      <div className="row-actions" style={{ marginTop: "1rem" }}>
        <button
          type="button"
          className="secondary small"
          disabled={status.cached_reads === 0}
          onClick={() => { clearCache(); push("Cached public reads cleared.", "success"); }}
        >
          <RollingLabel>Clear cached reads</RollingLabel>
        </button>
        <button
          type="button"
          className="ghost small"
          disabled={status.conflicts === 0}
          onClick={() => { clearConflicts(); push("Conflict list cleared.", "success"); }}
        >
          <RollingLabel>Clear conflict list</RollingLabel>
        </button>
      </div>
    </section>
  );
}
