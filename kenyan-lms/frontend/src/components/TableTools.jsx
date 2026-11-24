// Presentation-only controls shared by admin list pages. Search, page size and
// page state live in useTableControls so each page keeps its own data logic.
export function TableToolbar({ title = "records", controls, extra, onRefresh }) {
  return (
    <div className="table-toolbar">
      <label className="table-search">
        <span>Search {title.toLowerCase()}</span>
        <input
          type="search"
          value={controls.query}
          placeholder="Search all displayed fields"
          onChange={(event) => controls.changeQuery(event.target.value)}
        />
      </label>
      <div className="table-toolbar-meta">
        <span>{controls.filteredRows.length} record{controls.filteredRows.length === 1 ? "" : "s"}</span>
        {extra}
        <label className="inline-filter">
          Rows per page
          <select value={controls.pageSize} onChange={(event) => controls.changePageSize(event.target.value)}>
            {[10, 25, 50, 100].map((size) => <option key={size} value={size}>{size}</option>)}
          </select>
        </label>
        {onRefresh && <button className="ghost small" onClick={onRefresh}>Refresh</button>}
      </div>
    </div>
  );
}

export function TablePagination({ controls }) {
  if (controls.filteredRows.length === 0 || controls.totalPages <= 1) return null;
  return (
    <div className="table-pagination" aria-label="Table pagination">
      <button className="ghost small" disabled={controls.page <= 1} onClick={() => controls.setPage(controls.page - 1)}>Previous</button>
      <span>Page {controls.page} of {controls.totalPages}</span>
      <button className="ghost small" disabled={controls.page >= controls.totalPages} onClick={() => controls.setPage(controls.page + 1)}>Next</button>
    </div>
  );
}
