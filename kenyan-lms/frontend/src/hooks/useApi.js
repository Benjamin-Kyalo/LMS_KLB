import { useCallback, useEffect, useMemo, useState } from "react";
import { listAll, api } from "../services/api";

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
  return { data, loading, error, reload };
}

// Server-driven catalogue data. Unlike useList(), this never calls listAll():
// paging, filtering, searching and sorting are decided by the API so large
// public catalogues do not have to be downloaded in full.
export function usePagedResource(path, initial = {}) {
  const [data, setData] = useState({ results: [], count: 0, next: null, previous: null });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(initial.page || 1);
  const [query, setQueryState] = useState(initial.query || "");
  const [sort, setSortState] = useState(initial.sort || "title");
  const [filters, setFiltersState] = useState(initial.filters || {});
  const initialFiltersKey = JSON.stringify(initial.filters || {});

  const requestParams = useMemo(() => ({
    page,
    page_size: initial.pageSize || 12,
    q: query,
    ordering: sort,
    ...JSON.parse(initialFiltersKey),
    ...filters,
  }), [page, initial.pageSize, query, sort, initialFiltersKey, filters]);

  const paramsKey = JSON.stringify(requestParams);

  const reload = useCallback(async () => {
    if (!path) {
      setData({ results: [], count: 0, next: null, previous: null });
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      Object.entries(JSON.parse(paramsKey)).forEach(([key, value]) => {
        if (value !== "" && value !== null && value !== undefined) params.set(key, String(value));
      });
      const suffix = params.toString();
      setData(await api.get(suffix ? `${path}?${suffix}` : path));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [path, paramsKey]);

  useEffect(() => { reload(); }, [reload]);

  function resetPage(setter) {
    return (value) => { setter(value); setPage(1); };
  }

  return {
    data,
    results: data.results || [],
    count: data.count || 0,
    next: data.next,
    previous: data.previous,
    loading,
    error,
    page,
    setPage,
    query,
    setQuery: resetPage(setQueryState),
    sort,
    setSort: resetPage(setSortState),
    filters,
    setFilters: (nextFilters) => {
      setFiltersState((previous) => ({
        ...previous,
        ...(typeof nextFilters === "function" ? nextFilters(previous) : nextFilters),
      }));
      setPage(1);
    },
    setFilter: (key, value) => {
      setFiltersState((previous) => ({ ...previous, [key]: value }));
      setPage(1);
    },
    reload,
  };
}
