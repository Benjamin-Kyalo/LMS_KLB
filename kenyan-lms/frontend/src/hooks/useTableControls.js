import { useMemo, useState } from "react";

// Shared client-side search and pagination for admin lists. The API already
// returns institution-scoped records; this only shapes how they are displayed.
export default function useTableControls(rows) {
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const filteredRows = useMemo(() => {
    const term = query.trim().toLowerCase();
    if (!term) return rows || [];
    return (rows || []).filter((row) => JSON.stringify(row).toLowerCase().includes(term));
  }, [rows, query]);

  const totalPages = Math.max(1, Math.ceil(filteredRows.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const visibleRows = filteredRows.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  function changeQuery(value) {
    setQuery(value);
    setPage(1);
  }

  function changePageSize(value) {
    setPageSize(Number(value));
    setPage(1);
  }

  return {
    query, changeQuery,
    page: currentPage, setPage,
    pageSize, changePageSize,
    filteredRows, visibleRows, totalPages,
  };
}
