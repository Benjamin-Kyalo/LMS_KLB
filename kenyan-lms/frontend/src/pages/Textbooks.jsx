import { useState } from "react";
import { Link } from "react-router-dom";
import { useList } from "../hooks/useApi";
import { api } from "../services/api";
import Modal from "../components/Modal";
import Loading from "../components/Loading";
import { statusTag } from "../utilities/format";

export default function Textbooks({ resourcesTo = "/resources" }) {
  // The catalogue endpoint only returns published titles that this
  // institution has an active licence for.
  const { data, loading, error, reload } = useList("/content/available/");
  const [detail, setDetail] = useState(null);
  const [detailError, setDetailError] = useState(null);

  async function open(id) {
    setDetailError(null);
    try { setDetail(await api.get(`/content/textbooks/${id}/`)); }
    catch (err) { setDetailError(err.message); }
  }

  if (loading) return <Loading />;

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">Digital publishing</div>
          <h1>Textbook library</h1>
        </div>
        <div className="actions"><button className="secondary" onClick={reload}>Refresh catalogue</button></div>
      </div>

      {error && <div className="notice error">{error}</div>}
      {!error && data.length === 0 && (
        <div className="panel panel-pad" style={{ textAlign: "center", padding: "2rem" }}>
          <h3>No licensed textbooks available yet</h3>
          <p className="muted">Published titles appear here once your institution has an active content licence.</p>
          <Link to={resourcesTo} className="button-link">Browse learning resources →</Link>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(260px,1fr))", gap: "1rem" }}>
        {data.map((book) => (
          <div key={book.id} className="panel panel-pad">
            <div className="overline">{book.publisher_name || "KLB"}</div>
            <h3 style={{ marginBottom: "0.3rem" }}>{book.title}</h3>
            <p className="muted" style={{ fontSize: "0.85rem" }}>{book.subject_name || "General"} · {book.chapter_count} chapters</p>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "0.6rem" }}>
              {statusTag(book.status)}
              <button className="secondary small" onClick={() => open(book.id)}>Open</button>
            </div>
          </div>
        ))}
      </div>

      {detailError && <div className="notice error" style={{ marginTop: "1rem" }}>{detailError}</div>}

      {detail && (
        <Modal title={detail.title} onClose={() => setDetail(null)}>
          <p className="muted">{detail.description || "No description provided."}</p>
          {(detail.chapters || []).length === 0 && <p className="muted">This title has no chapters yet.</p>}
          {(detail.chapters || []).map((chapter) => (
            <div key={chapter.id} style={{ borderTop: "1px solid var(--line)", paddingTop: "0.6rem", marginTop: "0.6rem" }}>
              <strong>Chapter {chapter.chapter_number}: {chapter.title}</strong>
              <div className="muted" style={{ fontSize: "0.85rem" }}>
                {(chapter.exercises || []).length} exercises · {(chapter.resources || []).length} resources
              </div>
            </div>
          ))}
          <div className="form-actions">
            <button type="button" className="ghost" onClick={() => setDetail(null)}>Close</button>
          </div>
        </Modal>
      )}
    </section>
  );
}
