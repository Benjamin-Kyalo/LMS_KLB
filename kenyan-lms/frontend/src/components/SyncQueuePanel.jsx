import { useCallback, useEffect, useState } from "react";
import { useSyncQueue } from "../hooks/useSyncQueue";
import { conflicted } from "../services/offlineQueue";

// Long API paths would push the action buttons out of a narrow sidebar.
function shortPath(path, max = 60) {
  const value = String(path ?? "");
  return value.length > max ? `…${value.slice(-(max - 1))}` : value;
}

// Manual review for queued mutations the server rejected as conflicts.
// Mount once in a layout; no props are required.
export default function SyncQueuePanel({ className = "" }) {
  const { pending, conflicts, hasConflicts, message, syncing, syncNow, resolve } = useSyncQueue();
  const [items, setItems] = useState([]);
  const [status, setStatus] = useState("");
  const [busyId, setBusyId] = useState(null);

  const load = useCallback(async () => {
    try { setItems(await conflicted()); } catch { setItems([]); }
  }, []);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    const reload = () => load();
    const events = ["klb:sync-conflict", "klb:sync-conflict-resolved", "klb:synced", "klb:queued"];
    events.forEach((name) => window.addEventListener(name, reload));
    return () => events.forEach((name) => window.removeEventListener(name, reload));
  }, [load]);

  const act = async (id, strategy, doneMessage) => {
    setBusyId(id);
    setStatus("");
    try {
      const result = await resolve(id, strategy);
      setStatus(result.ok ? doneMessage : `Could not resolve this change: ${result.error?.message || "unknown error"}`);
    } catch (err) {
      setStatus(`Could not resolve this change: ${err.message}`);
    } finally {
      setBusyId(null);
      await load();
    }
  };

  return (
    <section className={`panel panel-pad ${className}`.trim()} aria-labelledby="sync-queue-heading">
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
        <h2 id="sync-queue-heading" style={{ margin: 0 }}>Offline changes</h2>
        <span className="tag info">{pending} pending</span>
        <span className={hasConflicts ? "tag warn" : "tag"}>
          {conflicts} conflict{conflicts === 1 ? "" : "s"}
        </span>
      </div>

      <div aria-live="polite" className="muted" style={{ marginTop: "0.5rem", minHeight: "1.2em" }}>
        {status || message || ""}
      </div>

      {!hasConflicts && items.length === 0 && (
        <p className="notice success" style={{ marginTop: "0.75rem" }}>
          No conflicts. Queued changes will sync automatically when you are back online.
        </p>
      )}

      {pending > 0 && !hasConflicts && (
        <button className="ghost small" style={{ marginTop: "0.75rem" }} onClick={syncNow} disabled={syncing}>
          {syncing ? "Sending…" : "Sync now"}
        </button>
      )}

      {items.length > 0 && (
        <ul style={{ listStyle: "none", margin: "0.75rem 0 0", padding: 0, display: "grid", gap: "0.75rem" }}>
          {items.map((item) => {
            const details = item.conflictDetails || {};
            const errorText = details.message || item.lastError || "The server has a newer copy of this record.";
            const busy = busyId === item.id;
            return (
              <li key={item.id} className="notice warn" aria-label={`Conflict on ${item.method} ${item.path}`}>
                <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
                  <code className="mono">{item.method} {shortPath(item.path)}</code>
                  <span className="tag warn">{details.code || "conflict"}</span>
                </div>
                <p style={{ margin: "0.4rem 0" }}>{errorText}</p>
                <p className="muted" style={{ margin: "0 0 0.6rem" }}>
                  Your saved change was not sent. Retrying sends it again; using the server copy or discarding drops your local change and keeps the server version.
                </p>
                <div className="row-actions">
                  <button
                    className="info small"
                    disabled={busy}
                    aria-busy={busy}
                    onClick={() => act(item.id, "retry", "Saved change retried. It will sync when the server accepts it.")}
                  >
                    Retry
                  </button>
                  {details.server?.updated_at && (
                    <button
                      className="secondary small"
                      disabled={busy}
                      aria-busy={busy}
                      onClick={() => act(item.id, "rebase", "Retried against the current server version.")}
                    >
                      Use current version
                    </button>
                  )}
                  <button
                    className="secondary small"
                    disabled={busy}
                    aria-busy={busy}
                    onClick={() => act(item.id, "discard", "Server copy kept — your local change was dropped.")}
                  >
                    Use server copy
                  </button>
                  <button
                    className="ghost danger small"
                    disabled={busy}
                    aria-busy={busy}
                    title="Also drops your local change and keeps the server copy"
                    onClick={() => act(item.id, "discard", "Local change discarded — the server copy is kept.")}
                  >
                    Discard
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
