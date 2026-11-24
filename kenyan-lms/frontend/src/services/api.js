// Single place for every HTTP call to the Django backend.
// Reads go straight to the network (the service worker caches responses).
// Mutations attempted while offline are queued in IndexedDB and replayed on
// reconnection. Authentication calls are never queued.

import { all, enqueue, remove, update } from "./offlineQueue";

const BASE = import.meta.env.VITE_API_BASE_URL || "/api";
const QUEUEABLE = new Set(["POST", "PATCH", "PUT", "DELETE"]);

export class ApiError extends Error {
  constructor(message, status, details) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

// A server-side version conflict: the local change is still valid, but the
// server holds a newer copy of the same resource. Try a safe rebase first;
// unresolved conflicts stay in the queue for manual review.
export class ConflictError extends ApiError {
  constructor(message, status, details, server) {
    super(message, status, details);
    this.server = server;
  }
}

function describeConflict(err) {
  if (err instanceof ConflictError) {
    return {
      status: err.status,
      message: err.message,
      server: err.server,
      code: err.details?.code,
    };
  }
  if (err instanceof ApiError) {
    return {
      status: err.status,
      message: err.message,
      server: undefined,
      code: err.details?.code,
    };
  }
  return {
    status: null,
    message: err?.message || "Request failed",
    server: undefined,
    code: undefined,
  };
}

function conflictPatch(item, err, prefix = "Conflict") {
  const details = describeConflict(err);
  const label = details.status == null ? "network" : `HTTP ${details.status}`;
  return {
    conflict: true,
    conflictDetails: details,
    attempts: (item.attempts || 0) + 1,
    lastError: `${prefix} (${label}): ${details.message}`,
  };
}

// Safe automatic resolution: when the server supplied its current version we
// replay the saved change once against that version (optimistic rebase). This
// never overwrites server data with a stale copy. If the server version moved
// again, the change stays in the queue for a human decision.
async function rebaseConflict(item, err) {
  const details = describeConflict(err);
  const method = String(item.method || "").toUpperCase();
  const serverVersion = details.server?.updated_at;
  if (!serverVersion || !["PATCH", "PUT", "DELETE"].includes(method)) {
    return { resolved: false, attempted: false };
  }

  const headers = { ...(item.headers || {}), "If-Match": serverVersion };
  try {
    await send(item.path, {
      method,
      body: method === "DELETE" ? undefined : item.body ?? undefined,
      headers,
    });
    await remove(item.id);
    return { resolved: true, attempted: true };
  } catch (retryErr) {
    // A conflicting DELETE for an already-removed record is already resolved.
    if (method === "DELETE" && retryErr instanceof ApiError && retryErr.status === 404) {
      await remove(item.id);
      return { resolved: true, attempted: true };
    }
    return { resolved: false, attempted: true };
  }
}

function getToken() {
  return localStorage.getItem("klb_token");
}

function notify(name, detail) {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent(name, { detail }));
  }
}

// DRF returns absolute pagination links. Accept those, API-prefixed paths and
// plain resource paths without ever producing "/apihttp://..." or "/api/api/...".
function fullUrl(path) {
  if (/^https?:\/\//i.test(path)) return path;
  const baseIsAbsolute = /^https?:\/\//i.test(BASE);
  const basePath = new URL(BASE, "http://local.invalid").pathname.replace(/\/$/, "");
  if (baseIsAbsolute) {
    if (path.startsWith(`${basePath}/`)) return BASE.replace(/\/$/, "") + path.slice(basePath.length);
    return BASE.replace(/\/$/, "") + "/" + path.replace(/^\//, "");
  }
  if (path === basePath || path.startsWith(`${basePath}/`)) return path;
  return BASE + (path.startsWith("/") ? path : "/" + path);
}

// Low-level send. Throws ApiError for HTTP failures and TypeError for
// network failures, so the caller can tell them apart.
async function send(path, { method = "GET", body, headers = {} } = {}) {
  const token = getToken();
  const isForm = typeof FormData !== "undefined" && body instanceof FormData;
  const response = await fetch(fullUrl(path), {
    method,
    headers: {
      // FormData supplies its own boundary; setting JSON here breaks uploads.
      ...(isForm ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: `Token ${token}` } : {}),
      ...headers,
    },
    body: isForm ? body : body !== undefined ? JSON.stringify(body) : undefined,
  });

  let data = null;
  const text = await response.text();
  if (text) {
    try { data = JSON.parse(text); } catch { data = { detail: text }; }
  }

  const message = (data && (data.detail || data.non_field_errors?.[0])) || response.statusText;
  // 409 is the standard signal, but a DRF view may flag a stale write with a
  // different status as long as the JSON body carries code="conflict".
  if (response.status === 409 || data?.code === "conflict") {
    throw new ConflictError(message, response.status, data, data?.server);
  }
  if (!response.ok) {
    throw new ApiError(message, response.status, data);
  }
  return data;
}

function isNetworkFailure(err) {
  return err instanceof TypeError || err?.name === "TypeError";
}

export async function request(path, options = {}) {
  const method = options.method || "GET";
  try {
    return await send(path, options);
  } catch (err) {
    const canQueue =
      QUEUEABLE.has(method) &&
      !path.startsWith("/auth/") &&
      Boolean(getToken()) &&
      isNetworkFailure(err);
    if (!canQueue) throw err;

    const item = await enqueue({ path, method, body: options.body, headers: options.headers });
    notify("klb:queued", item);
    return { queued: true, id: item.id };
  }
}

// Replay queued changes in order. A stale-write conflict is first retried
// against the server's current version; if that still conflicts the change is
// flagged for manual review and left in the queue. Other server rejections are
// recorded; a second network failure stops the drain so the rest retry later.
export async function syncPending() {
  const pending = await all();
  let synced = 0;
  let failed = 0;
  let conflicts = 0;
  let autoResolved = 0;
  for (const item of pending) {
    try {
      await send(item.path, { method: item.method, body: item.body ?? undefined, headers: item.headers });
      await remove(item.id);
      synced++;
    } catch (err) {
      if (err instanceof ConflictError) {
        const rebase = await rebaseConflict(item, err);
        if (rebase.resolved) {
          autoResolved++;
          notify("klb:sync-conflict-resolved", {
            id: item.id,
            strategy: "rebase",
            ok: true,
            automatic: true,
          });
          continue;
        }
        const patch = conflictPatch(
          item, err, rebase.attempted ? "Automatic rebase failed" : "Conflict"
        );
        await update(item.id, patch);
        conflicts++;
        notify("klb:sync-conflict", {
          item: { ...item, ...patch },
          details: patch.conflictDetails,
        });
      } else if (err instanceof ApiError) {
        await update(item.id, {
          attempts: (item.attempts || 0) + 1,
          lastError: `HTTP ${err.status}: ${err.message}`,
        });
        failed++;
      } else {
        break; // still offline - leave the rest in the queue
      }
    }
  }
  if (synced > 0) notify("klb:synced", { synced, failed, conflicts, autoResolved });
  return { synced, failed, conflicts, autoResolved };
}

// How many queued mutations are waiting for a human decision.
export async function conflictCount() {
  const rows = await all();
  return rows.filter((row) => row.conflict).length;
}

// Manually resolve a conflicted queue entry. "retry" re-sends the saved body,
// "discard" drops the local change, and "replace" re-sends replacementBody.
export async function resolveConflict(id, strategy, replacementBody) {
  const settle = (ok, error) => {
    notify("klb:sync-conflict-resolved", { id, strategy, ok });
    return error === undefined ? { ok } : { ok, error };
  };

  const [item] = (await all()).filter((row) => row.id === id);
  if (!item) return settle(false, new Error("That queued change is no longer available."));

  if (strategy === "discard") {
    await remove(id);
    return settle(true);
  }

  if (strategy === "rebase") {
    const details = item.conflictDetails || {};
    const synthetic = new ConflictError(
      details.message || "This record changed on the server.",
      details.status || 409,
      details,
      details.server,
    );
    const rebase = await rebaseConflict(item, synthetic);
    if (!rebase.resolved && rebase.attempted) {
      await update(item.id, conflictPatch(item, synthetic, "Automatic rebase failed"));
    }
    return settle(
      rebase.resolved,
      rebase.resolved
        ? undefined
        : new Error("The server version moved again. Review this change manually."),
    );
  }

  if (strategy !== "retry" && strategy !== "replace") {
    return settle(false, new Error(`Unknown conflict strategy: ${strategy}`));
  }

  const body = strategy === "replace" ? replacementBody : item.body ?? undefined;
  await update(id, { conflict: false, conflictDetails: null });
  try {
    await send(item.path, { method: item.method, body, headers: item.headers });
    await remove(id);
    return settle(true);
  } catch (err) {
    await update(id, conflictPatch(item, err, "Conflict retry failed"));
    return settle(false, err instanceof Error ? err : new Error(String(err)));
  }
}

export const api = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: "POST", body }),
  patch: (path, body) => request(path, { method: "PATCH", body }),
  del: (path) => request(path, { method: "DELETE" }),
  // File uploads need a real network connection and cannot be replayed from
  // the JSON queue, so they deliberately bypass request().
  upload: async (path, formData, method = "PATCH") => {
    if (typeof navigator !== "undefined" && !navigator.onLine) {
      throw new Error("Logo upload needs an internet connection. Try again when online.");
    }
    return send(path, { method, body: formData });
  },
};

// DRF list endpoints are paginated. This helper always returns an array.
export async function listAll(path) {
  let next = path;
  const items = [];
  while (next) {
    const data = await api.get(next);
    if (Array.isArray(data)) return data;
    items.push(...(data.results || []));
    // Keep the path (including /api) and let fullUrl() decide how to prefix it.
    next = data.next ? new URL(data.next, window.location.origin).pathname + new URL(data.next, window.location.origin).search : null;
  }
  return items;
}
