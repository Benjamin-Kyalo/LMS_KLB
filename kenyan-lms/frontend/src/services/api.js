// Single place for every HTTP call to the Django backend.
// Reads and mutations go straight to the network; failed requests throw.

const BASE = import.meta.env.VITE_API_BASE_URL || "/api";

export class ApiError extends Error {
  constructor(message, status, details) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

// Session authentication uses an HttpOnly cookie plus a readable CSRF cookie.
// The token is also returned after login so the first mutation can proceed
// before the browser has finished writing the cookie.
let memoryCsrfToken = "";

export function setCsrfToken(token) {
  memoryCsrfToken = token || "";
}

export function getCsrfToken() {
  if (memoryCsrfToken) return memoryCsrfToken;
  if (typeof document === "undefined") return "";
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
  memoryCsrfToken = match ? decodeURIComponent(match[1]) : "";
  return memoryCsrfToken;
}

const CSRF_METHODS = new Set(["POST", "PATCH", "PUT", "DELETE"]);

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

// DRF validation errors are usually field keyed, for example
// { image: "Use a photo at least 640×360 pixels." }. Surface that message
// instead of the generic "Bad Request" status text.
function firstMessage(value) {
  if (typeof value === "string") return value;
  if (Array.isArray(value)) return value.length ? firstMessage(value[0]) : "";
  if (!value || typeof value !== "object") return "";
  for (const key of ["detail", "non_field_errors"]) {
    if (value[key]) {
      const found = firstMessage(value[key]);
      if (found) return found;
    }
  }
  for (const item of Object.values(value)) {
    const found = firstMessage(item);
    if (found) return found;
  }
  return "";
}

function apiMessage(data, fallback) {
  if (!data || typeof data !== "object" || Array.isArray(data)) {
    return firstMessage(data) || fallback;
  }
  for (const key of ["detail", "non_field_errors"]) {
    if (data[key]) {
      const found = firstMessage(data[key]);
      if (found) return found;
    }
  }
  for (const [key, value] of Object.entries(data)) {
    const found = firstMessage(value);
    if (found) return `${key.replace(/_/g, " ")}: ${found}`;
  }
  return fallback;
}

// Low-level send. Throws ApiError for HTTP failures and TypeError for network
// failures.
async function send(path, { method = "GET", body, headers = {} } = {}) {
  const isForm = typeof FormData !== "undefined" && body instanceof FormData;
  const csrfToken = CSRF_METHODS.has(method.toUpperCase()) ? getCsrfToken() : "";
  const response = await fetch(fullUrl(path), {
    method,
    credentials: "include",
    headers: {
      // FormData supplies its own boundary; setting JSON here breaks uploads.
      ...(isForm ? {} : { "Content-Type": "application/json" }),
      ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
      ...headers,
    },
    body: isForm ? body : body !== undefined ? JSON.stringify(body) : undefined,
  });

  let data = null;
  const text = await response.text();
  if (text) {
    try { data = JSON.parse(text); } catch { data = { detail: text }; }
  }

  const message = apiMessage(data, response.statusText);
  if (!response.ok) {
    throw new ApiError(message, response.status, data);
  }
  return data;
}

export async function request(path, options = {}) {
  return send(path, options);
}

export const api = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: "POST", body }),
  patch: (path, body) => request(path, { method: "PATCH", body }),
  del: (path) => request(path, { method: "DELETE" }),
  upload: async (path, formData, method = "PATCH") => {
    if (typeof navigator !== "undefined" && !navigator.onLine) {
      throw new Error("Uploads need a network connection. Try again.");
    }
    return send(path, { method, body: formData });
  },
  // Authenticated downloads fetch a blob so the session cookie is included.
  download: async (path, suggestedName = "download") => {
    if (typeof navigator !== "undefined" && !navigator.onLine) {
      throw new ApiError("Downloads need a network connection. Try again.", 0);
    }
    const response = await fetch(fullUrl(path), { credentials: "include" });
    if (!response.ok) {
      let data = null;
      const text = await response.text();
      if (text) {
        try { data = JSON.parse(text); } catch { data = { detail: text }; }
      }
      throw new ApiError(apiMessage(data, response.statusText), response.status, data);
    }
    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = objectUrl;
    anchor.download = suggestedName;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(objectUrl), 0);
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
