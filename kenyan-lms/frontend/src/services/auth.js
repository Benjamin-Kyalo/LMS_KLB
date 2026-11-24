import { api } from "./api";

export function storeLogin(data) {
  localStorage.setItem("klb_token", data.token);
  localStorage.setItem("klb_user", JSON.stringify(data.user));
  return data;
}

export async function login(username, password) {
  const data = await api.post("/auth/login/", { username, password });
  return storeLogin(data);
}

export async function logout() {
  try { await api.post("/auth/logout/", {}); } catch { /* token may already be gone */ }
  localStorage.removeItem("klb_token");
  localStorage.removeItem("klb_user");
}

export function storedUser() {
  const raw = localStorage.getItem("klb_user");
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    localStorage.removeItem("klb_user");
    return null;
  }
}

export function isLoggedIn() {
  return Boolean(localStorage.getItem("klb_token"));
}
