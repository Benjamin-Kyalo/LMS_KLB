import { useCallback, useEffect, useRef, useState } from "react";
import { conflictCount, resolveConflict, syncPending } from "../services/api";
import { count } from "../services/offlineQueue";
import { useOnlineStatus } from "./useOnlineStatus";

// Tracks queued mutations and replays them automatically on reconnection.
export function useSyncQueue() {
  const [pending, setPending] = useState(0);
  const [conflicts, setConflicts] = useState(0);
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState(null);
  const online = useOnlineStatus();
  const wasOnline = useRef(online);

  const refresh = useCallback(async () => {
    try { setPending(await count()); } catch { setPending(0); }
    try { setConflicts(await conflictCount()); } catch { setConflicts(0); }
  }, []);

  const syncNow = useCallback(async () => {
    if (typeof navigator !== "undefined" && !navigator.onLine) {
      setMessage("Still offline — nothing was sent.");
      return { synced: 0, failed: 0, conflicts: 0, autoResolved: 0 };
    }
    setSyncing(true);
    setMessage(null);
    try {
      const result = await syncPending();
      const auto = result.autoResolved
        ? `${result.autoResolved} conflict(s) resolved against the current server version. `
        : "";
      setMessage(
        result.synced || result.autoResolved
          ? `${auto}${result.synced} change(s) sent.${result.conflicts ? ` ${result.conflicts} need review.` : ""}`
          : result.conflicts
            ? `${result.conflicts} change(s) need review before they can sync.`
            : result.failed
              ? "Some changes were rejected by the server."
              : "Nothing to send."
      );
      await refresh();
      return result;
    } catch (err) {
      setMessage(err.message);
      return { synced: 0, failed: 0, conflicts: 0, autoResolved: 0 };
    } finally {
      setSyncing(false);
    }
  }, [refresh]);

  // Resolve a single conflict and keep both counters in step with the queue.
  const resolve = useCallback(async (id, strategy, replacementBody) => {
    const result = await resolveConflict(id, strategy, replacementBody);
    await refresh();
    setMessage(
      result.ok
        ? "Conflict resolved — the change was removed from the queue."
        : `Could not resolve the conflict: ${result.error?.message || "unknown error"}`
    );
    return result;
  }, [refresh]);

  useEffect(() => { refresh(); }, [refresh]);

  useEffect(() => {
    const onQueued = () => { setMessage(null); refresh(); };
    const onSynced = () => refresh();
    const onConflict = () => {
      refresh();
      setMessage("A queued change conflicts with the server and needs your review.");
    };
    const onResolved = () => refresh();
    window.addEventListener("klb:queued", onQueued);
    window.addEventListener("klb:synced", onSynced);
    window.addEventListener("klb:sync-conflict", onConflict);
    window.addEventListener("klb:sync-conflict-resolved", onResolved);
    return () => {
      window.removeEventListener("klb:queued", onQueued);
      window.removeEventListener("klb:synced", onSynced);
      window.removeEventListener("klb:sync-conflict", onConflict);
      window.removeEventListener("klb:sync-conflict-resolved", onResolved);
    };
  }, [refresh]);

  // Auto-sync only on an offline -> online transition, not on every render.
  useEffect(() => {
    if (online && !wasOnline.current) syncNow();
    wasOnline.current = online;
  }, [online, syncNow]);

  return {
    pending,
    syncing,
    message,
    syncNow,
    refresh,
    conflicts,
    hasConflicts: conflicts > 0,
    resolve,
  };
}
