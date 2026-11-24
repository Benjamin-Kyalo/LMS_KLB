import SyncQueuePanel from "../components/SyncQueuePanel";

// Offline changes are kept per browser. Stale writes are retried once against
// the current server version; unresolved conflicts stay here for explicit review.
export default function SyncQueue() {
  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">Offline support</div>
          <h1>Sync queue</h1>
        </div>
      </div>
      <div className="notice" style={{ marginBottom: "1rem" }}>
        Changes made while offline are stored in this browser until a connection returns.
        If a change is stale, the app first retries it against the current server version. If
        it still conflicts, it stays here for you to retry or discard — a stale copy never
        silently overwrites newer school data.
      </div>
      <SyncQueuePanel />
    </section>
  );
}
