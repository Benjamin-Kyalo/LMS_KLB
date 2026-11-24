import { useEffect, useState } from "react";
import { useSyncQueue } from "../hooks/useSyncQueue";

// Small inline status shown at the top of the dashboard shell.
export default function SyncStatus() {
  const { pending, syncing, message, syncNow } = useSyncQueue();
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => setDismissed(false), [message, pending]);

  if (dismissed || (pending === 0 && !message)) return null;

  return (
    <div className="notice info" style={{ marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.75rem", justifyContent: "space-between" }}>
      <span>
        {pending > 0
          ? `${pending} change${pending === 1 ? "" : "s"} waiting to sync.`
          : message}
      </span>
      <span style={{ display: "flex", gap: "0.4rem" }}>
        {pending > 0 && (
          <button className="info small" onClick={syncNow} disabled={syncing}>
            {syncing ? "Sending…" : "Sync now"}
          </button>
        )}
        <button className="ghost small" onClick={() => setDismissed(true)}>Dismiss</button>
      </span>
    </div>
  );
}
