// Narrow low-bandwidth support for an already-loaded web page.
// There is no service worker, no PWA shell and no native wrapper. This module
// caches only public allowlisted reads and queues only allowlisted writes. It
// never stores cookies, CSRF tokens, credentials or person-like fields.

const PREFIX = "klb_low_bandwidth_v1";
const CACHE_KEY = `${PREFIX}:cache`;
const OUTBOX_KEY = `${PREFIX}:outbox`;
const CONFLICTS_KEY = `${PREFIX}:conflicts`;

const SENSITIVE_KEY = /password|secret|token|csrf|session|cookie|credential|learner|guardian|student|teacher|email|phone|mobile|address|national|admission|payer|card|account|reference|id[-_ ]?number|idnumber/i;
const CREDENTIAL_VALUE = /(?:bearer\s+\S+|eyJ[A-Za-z0-9_-]{10,})/i;

let clientConfig = null;
let configVersion = "";
const listeners = new Set();

function notify() {
  listeners.forEach((listener) => {
    try { listener(); } catch { /* A broken listener must not block sync. */ }
  });
}

export function subscribe(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function setClientConfig(config) {
  const next = config && typeof config === "object" ? config : null;
  const version = next?.version || "";
  if (configVersion && version && version !== configVersion) {
    // A changed ruleset invalidates saved public reads. Queued writes are kept
    // so a deliberate retry can still surface a conflict instead of losing data.
    writeJson(CACHE_KEY, []);
  }
  configVersion = version;
  clientConfig = next;
  notify();
}

export function getClientConfig() {
  return clientConfig;
}

function storage() {
  if (typeof window === "undefined") return null;
  try { return window.localStorage; } catch { return null; }
}

function readJson(key, fallback) {
  try {
    const raw = storage()?.getItem(key);
    if (!raw) return fallback;
    const parsed = JSON.parse(raw);
    return parsed ?? fallback;
  } catch {
    return fallback;
  }
}

function writeJson(key, value) {
  try {
    const store = storage();
    if (!store) return false;
    store.setItem(key, JSON.stringify(value));
    return true;
  } catch {
    return false;
  }
}

export function normalisePath(path) {
  const raw = String(path || "").split("?")[0];
  const withoutApi = raw.startsWith("/api/") ? raw.slice(4) : raw;
  const trimmed = withoutApi.replace(/^\/+/, "").replace(/\/+$/, "");
  return trimmed ? `/${trimmed}/` : "/";
}

function allowed(path, paths) {
  const candidate = normalisePath(path);
  return (Array.isArray(paths) ? paths : []).some((entry) => {
    const allowedPath = normalisePath(entry);
    return candidate === allowedPath
      || (allowedPath !== "/" && candidate.startsWith(allowedPath));
  });
}

export function isCacheable(path) {
  const offline = clientConfig?.offline;
  return Boolean(offline?.enabled && offline.read_cache?.enabled && allowed(path, offline.read_cache.paths));
}

export function isOutboxable(method, path) {
  const offline = clientConfig?.offline;
  const upper = String(method || "").toUpperCase();
  return Boolean(
    offline?.enabled && offline.outbox?.enabled
    && ["PATCH", "DELETE"].includes(upper)
    && allowed(path, offline.outbox.paths),
  );
}

function versionOf(data) {
  if (!data || typeof data !== "object") return null;
  if (typeof data.updated_at === "string") return data.updated_at;
  if (Array.isArray(data.results)) return versionOf(data.results[0]);
  if (Array.isArray(data)) return versionOf(data[0]);
  return null;
}

function sanitiseBody(value, key = "") {
  if (key && SENSITIVE_KEY.test(key)) {
    throw new Error("This change contains personal or credential data and cannot be queued.");
  }
  if (value === null || value === undefined) return value ?? null;
  if (typeof value === "string") {
    if (CREDENTIAL_VALUE.test(value)) {
      throw new Error("This change contains credential data and cannot be queued.");
    }
    return value;
  }
  if (typeof value !== "object") return value;
  if (Array.isArray(value)) return value.map((item) => sanitiseBody(item, key));
  const clean = {};
  Object.entries(value).forEach(([childKey, childValue]) => {
    clean[childKey] = sanitiseBody(childValue, childKey);
  });
  return clean;
}

function makeId() {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 9)}`;
}

function trim(items, limit, timeKey) {
  const safeLimit = Math.max(1, Number(limit) || 20);
  return [...items]
    .sort((a, b) => String(b[timeKey] || "").localeCompare(String(a[timeKey] || "")))
    .slice(0, safeLimit);
}

export function readCached(path) {
  if (!isCacheable(path)) return null;
  const maxAge = Number(clientConfig.offline.read_cache.max_age_seconds) || 3600;
  const cutoff = Date.now() - maxAge * 1000;
  const entry = readJson(CACHE_KEY, []).find((row) => normalisePath(row.path) === normalisePath(path));
  if (!entry || new Date(entry.saved_at).getTime() < cutoff) return null;
  return entry;
}

export function writeCached(path, data) {
  if (!isCacheable(path) || data === undefined || data === null) return false;
  const limit = Number(clientConfig.offline.read_cache.max_items) || 25;
  const rows = readJson(CACHE_KEY, []).filter((row) => normalisePath(row.path) !== normalisePath(path));
  rows.push({
    path: normalisePath(path),
    data,
    version: versionOf(data),
    saved_at: new Date().toISOString(),
  });
  const saved = writeJson(CACHE_KEY, trim(rows, limit, "saved_at"));
  if (saved) notify();
  return saved;
}

export function clearCache() {
  writeJson(CACHE_KEY, []);
  notify();
}

export function listOutbox() {
  const rows = readJson(OUTBOX_KEY, []);
  return Array.isArray(rows) ? rows : [];
}

export function enqueueWrite({ method, path, body = null, ifMatch = "" }) {
  if (!isOutboxable(method, path)) return null;
  const safeBody = sanitiseBody(body);
  const rows = listOutbox();
  const limit = Number(clientConfig.offline.outbox.max_items) || 20;
  const existing = rows.find((row) => row.method === method && normalisePath(row.path) === normalisePath(path));
  const item = {
    id: existing?.id || makeId(),
    method: String(method).toUpperCase(),
    path: normalisePath(path),
    body: safeBody,
    if_match: typeof ifMatch === "string" ? ifMatch : "",
    created_at: new Date().toISOString(),
  };
  const next = existing
    ? rows.map((row) => (row.id === existing.id ? item : row))
    : trim([...rows, item], limit, "created_at");
  if (!writeJson(OUTBOX_KEY, next)) return null;
  notify();
  return item;
}

export function removeOutboxItem(id) {
  writeJson(OUTBOX_KEY, listOutbox().filter((row) => row.id !== id));
  notify();
}

export function listConflicts() {
  const rows = readJson(CONFLICTS_KEY, []);
  return Array.isArray(rows) ? rows : [];
}

function addConflict({ method, path, message, server }) {
  const rows = listConflicts().filter(
    (row) => !(row.method === method && normalisePath(row.path) === normalisePath(path)),
  );
  rows.unshift({
    id: makeId(),
    method,
    path: normalisePath(path),
    message: message || "The server version changed.",
    server_updated_at: server?.updated_at || "",
    created_at: new Date().toISOString(),
  });
  writeJson(CONFLICTS_KEY, trim(rows, 20, "created_at"));
}

export function clearConflicts() {
  writeJson(CONFLICTS_KEY, []);
  notify();
}

export function dismissConflict(id) {
  writeJson(CONFLICTS_KEY, listConflicts().filter((row) => row.id !== id));
  notify();
}

export async function flushOutbox(sendRequest) {
  const outbox = clientConfig?.offline?.outbox;
  if (typeof sendRequest !== "function" || !clientConfig?.offline?.enabled || !outbox?.enabled) {
    return { sent: 0, conflicts: 0, kept: listOutbox().length };
  }
  if (typeof navigator !== "undefined" && navigator.onLine === false) {
    return { sent: 0, conflicts: 0, kept: listOutbox().length };
  }
  const queue = listOutbox();
  const kept = [];
  let sent = 0;
  let conflicts = 0;
  for (const item of queue) {
    try {
      const headers = item.if_match ? { "If-Match": item.if_match } : {};
      await sendRequest(item.path, {
        method: item.method,
        body: item.body === null ? undefined : item.body,
        headers,
      });
      sent += 1;
    } catch (error) {
      const statusCode = Number(error?.status) || 0;
      if (statusCode === 409) {
        addConflict({
          method: item.method,
          path: item.path,
          message: error.message || "The server version changed.",
          server: error.details?.server,
        });
        conflicts += 1;
      } else if (statusCode >= 400 && statusCode < 500) {
        addConflict({
          method: item.method,
          path: item.path,
          message: "The server rejected this queued change.",
        });
        conflicts += 1;
      } else {
        kept.push(item);
      }
    }
  }
  writeJson(OUTBOX_KEY, kept);
  notify();
  return { sent, conflicts, kept: kept.length };
}

export function lowBandwidthStatus() {
  return {
    cached_reads: readJson(CACHE_KEY, []).length,
    queued_writes: listOutbox().length,
    conflicts: listConflicts().length,
  };
}
