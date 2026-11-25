import { useState } from "react";
import { BookOpen, Search } from "lucide-react";
import { usePagedResource } from "../hooks/useApi";
import RollingLabel from "./RollingLabel";

const PAGE_SIZE = 12;

function coverInitials(title = "") {
  return String(title)
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0]?.toUpperCase() || "")
    .join("");
}

function contextLine(book) {
  return [book.level_name, book.subject_name, book.publisher_name]
    .filter(Boolean)
    .join(" · ");
}

function Pagination({ page, setPage, count, loading }) {
  const pages = Math.max(1, Math.ceil((count || 0) / PAGE_SIZE));
  if (loading && !count) return null;
  return (
    <nav className="book-pagination" aria-label="Book pages">
      <button
        className="ghost small"
        disabled={page <= 1}
        onClick={() => setPage(page - 1)}
        aria-label="Previous page of books"
      >
        Previous
      </button>
      <span>Page {page} of {pages} · {count} book{count === 1 ? "" : "s"}</span>
      <button
        className="ghost small"
        disabled={page >= pages}
        onClick={() => setPage(page + 1)}
        aria-label="Next page of books"
      >
        Next
      </button>
    </nav>
  );
}

function BookCard({ book, eager }) {
  const [coverFailed, setCoverFailed] = useState(false);
  const cover = book.cover_url && !coverFailed ? book.cover_url : "";
  return (
    <article className="book-card panel">
      <div className="book-cover">
        {cover ? (
          <img
            src={cover}
            alt={`Cover artwork for ${book.title}`}
            width="600"
            height="800"
            loading={eager ? "eager" : "lazy"}
            decoding="async"
            onError={() => setCoverFailed(true)}
          />
        ) : (
          <div className="book-cover-fallback" aria-hidden="true">
            <BookOpen size={28} strokeWidth={1.5} />
            <span className="book-cover-initials">{coverInitials(book.title)}</span>
          </div>
        )}
      </div>
      <div className="book-card-body">
        <div className="resource-card-tags">
          <span className="tag info">Book</span>
          <span className="tag">{book.access_label || "School access"}</span>
        </div>
        <h3>{book.title}</h3>
        {book.subtitle && <p className="book-subtitle">{book.subtitle}</p>}
        {contextLine(book) && (
          <p className="muted resource-card-context">{contextLine(book)}</p>
        )}
        {book.description && <p className="resource-card-copy">{book.description}</p>}
        <p className="book-meta">
          {book.chapter_count || 0} chapter{book.chapter_count === 1 ? "" : "s"} in this preview
        </p>
      </div>
    </article>
  );
}

// Anonymous catalogue preview. The API returns only published, non-expired
// book metadata. Chapter access and downloads stay behind school licence checks.
export default function PublicBookShelf({ overline, title, description }) {
  const books = usePagedResource("/content/public/books/", {
    pageSize: PAGE_SIZE,
    sort: "title",
  });
  const [refreshing, setRefreshing] = useState(false);

  async function refresh() {
    setRefreshing(true);
    try { await books.reload(); }
    finally { setRefreshing(false); }
  }

  return (
    <section className="book-shelf" aria-labelledby="public-books-heading">
      <div className="public-section-head">
        <div>
          {overline && <div className="overline">{overline}</div>}
          <h2 id="public-books-heading">{title}</h2>
          {description && <p>{description}</p>}
        </div>
        <button
          className="secondary"
          onClick={refresh}
          aria-label="Refresh books"
          aria-busy={refreshing}
          disabled={refreshing}
        >
          {refreshing ? "Refreshing…" : <RollingLabel>Refresh books</RollingLabel>}
        </button>
      </div>

      <div className="book-toolbar panel panel-pad">
        <label className="book-search">
          <span>Search books</span>
          <span className="book-search-input">
            <Search size={17} strokeWidth={1.8} aria-hidden="true" />
            <input
              type="search"
              value={books.query}
              placeholder="Title, subject or publisher"
              onChange={(event) => books.setQuery(event.target.value)}
            />
          </span>
        </label>
        {!books.loading && <span className="muted book-count">{books.count} available</span>}
      </div>

      {books.error && <div className="notice error">{books.error}</div>}

      {books.loading ? (
        <div className="panel panel-pad">Loading books…</div>
      ) : books.results.length === 0 ? (
        <div className="panel panel-pad">
          <h3>No books found</h3>
          <p className="muted">Try a different search, or check again after the catalogue is updated.</p>
        </div>
      ) : (
        <div className="book-grid">
          {books.results.map((book, index) => (
            <BookCard key={book.id} book={book} eager={index < 4} />
          ))}
        </div>
      )}

      <Pagination
        page={books.page}
        setPage={books.setPage}
        count={books.count}
        loading={books.loading}
      />
    </section>
  );
}
