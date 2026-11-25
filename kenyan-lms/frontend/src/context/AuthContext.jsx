import { createContext, useContext, useEffect, useState } from "react";
import { api } from "../services/api";
import { login as doLogin, logout as doLogout, storeLogin } from "../services/auth";

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    // Ensure the CSRF cookie exists for the first signed-in mutation, then
    // derive identity and roles from the server session on every page load.
    api.get("/auth/csrf/").catch(() => {});
    api.get("/auth/me/")
      .then((data) => { if (active) setUser(data); })
      .catch(() => { if (active) setUser(null); })
      .finally(() => { if (active) setRefreshing(false); });
    return () => { active = false; };
  }, []);

  async function signIn(username, password) {
    setLoading(true);
    setError(null);
    try {
      const data = await doLogin(username, password);
      setUser(data.user);
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }

  async function signOut() {
    await doLogout();
    setUser(null);
  }

  function signInWithData(data) {
    storeLogin(data);
    setUser(data.user);
    return data;
  }

  return (
    <AuthContext.Provider value={{ user, loading, refreshing, error, signIn, signOut, signInWithData, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
