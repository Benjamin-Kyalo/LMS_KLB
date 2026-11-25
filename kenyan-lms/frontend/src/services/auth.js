import { api, setCsrfToken } from "./api";

// Identity lives in the server session cookie. The browser never receives a
// long-lived bearer token and roles are always re-read from /auth/me/.
export function storeLogin(data) {
  if (data?.csrfToken) setCsrfToken(data.csrfToken);
  return data;
}

export async function login(username, password) {
  const data = await api.post("/auth/login/", { username, password });
  return storeLogin(data);
}

export async function logout() {
  try { await api.post("/auth/logout/", {}); } catch { /* session may already be gone */ }
  setCsrfToken("");
}
