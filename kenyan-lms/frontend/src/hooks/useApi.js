import { useCallback, useEffect, useState } from "react";
import { listAll, api } from "../services/api";

// Pages reload themselves after queued changes have been sent.
function useReloadOnSync(reload) {
  useEffect(() => {
    const handler = () => reload();
    window.addEventListener("klb:synced", handler);
    return () => window.removeEventListener("klb:synced", handler);
  }, [reload]);
}

// Load a list once, with reload support. Returns { data, loading, error, reload }.
export function useList(path) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try { setData(await listAll(path)); }
    catch (err) { setError(err.message); }
    finally { setLoading(false); }
  }, [path]);

  useEffect(() => { reload(); }, [reload]);
  useReloadOnSync(reload);
  return { data, loading, error, reload, setData };
}

export function useResource(path) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const reload = useCallback(async () => {
    if (!path) {
      setData(null);
      setLoading(false);
      setError(null);
      return;
    }
    setLoading(true);
    setError(null);
    try { setData(await api.get(path)); }
    catch (err) { setError(err.message); }
    finally { setLoading(false); }
  }, [path]);

  useEffect(() => { reload(); }, [reload]);
  useReloadOnSync(reload);
  return { data, loading, error, reload };
}
