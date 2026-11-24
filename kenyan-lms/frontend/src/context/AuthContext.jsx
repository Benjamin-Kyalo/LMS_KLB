import { createContext, useContext, useEffect, useState } from "react";
import { api } from "../services/api";
import { login as doLogin, logout as doLogout, storeLogin, storedUser } from "../services/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(storedUser());
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(Boolean(storedUser()));
  const [error, setError] = useState(null);

  useEffect(() => {
    // Refresh the profile from the server on load so roles stay current.
    if (user) {
      api.get("/auth/me/")
        .then(setUser)
        .catch(() => { /* keep cached user if the server is offline */ })
        .finally(() => setRefreshing(false));
    } else {
      setRefreshing(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
