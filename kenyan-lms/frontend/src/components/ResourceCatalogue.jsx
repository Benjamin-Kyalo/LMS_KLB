import { useState } from "react";
import { usePagedResource, useResource } from "../hooks/useApi";
import ResourceCard from "./ResourceCard";
import ResourceDetail from "./ResourceDetail";
import ResourceFilters from "./ResourceFilters";
import RollingLabel from "./RollingLabel";

function Pagination({ page, setPage, count, pageSize, loading }) {
  const pages = Math.max(1, Math.ceil((count || 0) / pageSize));
  if (loading && !count) return null;
  return (
    <nav className="resource-pagination" aria-label="Resource pages">
      <button
        className="ghost small"
        disabled={page <= 1}
        onClick={() => setPage(page - 1)}
        aria-label="Previous page"
      >
        Previous
      </button>
      <span>Page {page} of {pages} · {count} resource{count === 1 ? "" : "s"}</span>
      <button
        className="ghost small"
        disabled={page >= pages}
        onClick={() => setPage(page + 1)}
        aria-label="Next page"
      >
        Next
      </button>
    </nav>
  );
}

// One catalogue UI serves the public library and the authenticated portal.
// The endpoint decides visibility; this component only presents what it returns.
export default function ResourceCatalogue({
  endpoint, title, overline, description, className = "", headingLevel = "h1",
}) {
  const Heading = headingLevel === "h2" ? "h2" : "h1";
  const [selected, setSelected] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const facets = useResource("/content/facets/");
  const catalogue = usePagedResource(endpoint, { pageSize: 12, sort: "title" });
  const visibleFilters = {
    ...catalogue.filters,
    level: catalogue.filters.education_level || "",
    area: catalogue.filters.learning_area || "",
  };

  async function refresh() {
    setRefreshing(true);
    try { await catalogue.reload(); }
    finally { setRefreshing(false); }
  }

  function handleFilter(key, value) {
    // The filter labels are friendly; the API uses its own field names.
    if (key === "level") {
      catalogue.setFilters((previous) => ({ ...previous, education_level: value, learning_area: "" }));
      return;
    }
    if (key === "area") {
      catalogue.setFilter("learning_area", value);
      return;
    }
    catalogue.setFilter(key, value);
  }

  return (
    <section className={`resource-catalogue ${className}`}>
      <div className="page-head">
        <div>
          {overline && <div className="overline">{overline}</div>}
          <Heading>{title}</Heading>
          {description && <p className="muted">{description}</p>}
        </div>
        <button
          className="secondary"
          onClick={refresh}
          aria-label="Refresh resources"
          aria-busy={refreshing}
          disabled={refreshing}
        >
          {refreshing ? "Refreshing…" : <RollingLabel>Refresh resources</RollingLabel>}
        </button>
      </div>

      {facets.error && <div className="notice warn" role="alert">Filters are unavailable right now: {facets.error}</div>}
      <ResourceFilters
        facets={facets.data || {}}
        filters={visibleFilters}
        onFilter={handleFilter}
        query={catalogue.query}
        onQuery={catalogue.setQuery}
        sort={catalogue.sort}
        onSort={catalogue.setSort}
      />

      {catalogue.error && <div className="notice error" role="alert">{catalogue.error}</div>}

      {catalogue.loading ? (
        <div className="panel panel-pad" role="status">Loading resources…</div>
      ) : catalogue.results.length === 0 ? (
        <div className="panel panel-pad">
          <h2>No matching resources</h2>
          <p className="muted">Try a different level, area, keyword or search term.</p>
        </div>
      ) : (
        <div className="resource-grid">
          {catalogue.results.map((resource) => (
            <ResourceCard key={resource.id} resource={resource} onSelect={setSelected} />
          ))}
        </div>
      )}

      <Pagination
        page={catalogue.page}
        setPage={catalogue.setPage}
        count={catalogue.count}
        pageSize={12}
        loading={catalogue.loading}
      />

      {selected && <ResourceDetail resource={selected} onClose={() => setSelected(null)} />}
    </section>
  );
}
