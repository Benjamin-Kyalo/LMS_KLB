import { useState } from "react";
import { api } from "../services/api";
import Modal from "./Modal";
import RollingLabel from "./RollingLabel";

function safeHttpsUrl(value) {
  if (!value) return "";
  const raw = String(value);
  // Only absolute HTTPS URLs are accepted. Relative paths and anything with
  // markup or whitespace cannot accidentally become a clickable payload.
  if (!/^https:\/\//i.test(raw) || /[\s<>"'\\]/.test(raw)) return "";
  try {
    const parsed = new URL(raw);
    return parsed.protocol === "https:" ? parsed.href : "";
  } catch {
    return "";
  }
}

function safeImageUrl(value) {
  if (!value) return "";
  const raw = String(value);
  if (/^\/(images|media)\//.test(raw) && !/[\s<>"'\\]/.test(raw)) return raw;
  return safeHttpsUrl(raw);
}

function suggestedName(resource) {
  const extension = String(resource.resource_type || "").toLowerCase().replace(/[^a-z0-9]/g, "") || "file";
  return `${String(resource.title || "resource").replace(/[^a-z0-9-_ ]/gi, "").trim().replace(/\s+/g, "-")}.${extension}`;
}

// Preview panel for catalogue records. All URLs are server-built or validated;
// no client-supplied HTML is ever rendered.
export default function ResourceDetail({ resource, onClose }) {
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const [thumbFailed, setThumbFailed] = useState(false);
  if (!resource) return null;

  const embedUrl = safeHttpsUrl(resource.embed_url);
  const externalUrl = safeHttpsUrl(resource.external_url);
  const downloadUrl = resource.file_available ? resource.download_url : "";
  const thumbnailUrl = thumbFailed ? "" : safeImageUrl(resource.thumbnail_url);

  async function download() {
    setBusy(true);
    setError(null);
    try {
      await api.download(downloadUrl, suggestedName(resource));
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title={resource.title || "Resource"} onClose={onClose}>
      <div className="resource-detail">
        {thumbnailUrl && (
          <img
            className="resource-detail-thumbnail"
            src={thumbnailUrl}
            alt={`Thumbnail for ${resource.title}`}
            width="640"
            height="360"
            loading="lazy"
            decoding="async"
            onError={() => setThumbFailed(true)}
          />
        )}
        <div className="resource-card-tags">
          <span className="tag info">{resource.resource_type || "Resource"}</span>
          {resource.status && <span className="tag">{resource.status}</span>}
        </div>
        {resource.description && <p>{resource.description}</p>}

        <dl className="detail-list">
          {resource.education_level_name && <div><dt>Level</dt><dd>{resource.education_level_name}</dd></div>}
          {resource.learning_area_name && <div><dt>Learning area</dt><dd>{resource.learning_area_name}</dd></div>}
          {resource.subject_name && <div><dt>Subject</dt><dd>{resource.subject_name}</dd></div>}
          {resource.collection_name && <div><dt>Collection</dt><dd>{resource.collection_name}</dd></div>}
          {resource.size_kb > 0 && <div><dt>Size</dt><dd>{resource.size_kb} KB</dd></div>}
        </dl>

        {embedUrl && (
          <div className="resource-embed">
            <iframe
              src={embedUrl}
              title={`Preview of ${resource.title}`}
              sandbox="allow-scripts allow-presentation"
              referrerPolicy="no-referrer"
              loading="lazy"
              allowFullScreen
            />
          </div>
        )}

        {error && <div className="notice error" role="alert">{error}</div>}

        <div className="form-actions">
          {downloadUrl && (
            <button
              type="button"
              onClick={download}
              disabled={busy}
              aria-label={`Download ${resource.title} file`}
              aria-busy={busy}
            >
              {busy ? "Preparing…" : "Download file"}
            </button>
          )}
          {!downloadUrl && externalUrl && (
            <a
              className="button-link"
              href={externalUrl}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={`Open ${resource.title} (opens in a new tab)`}
            >
              Open external resource
            </a>
          )}
          {!downloadUrl && !externalUrl && !embedUrl && (
            <span className="muted">This resource has no previewable file.</span>
          )}
          <button type="button" className="ghost" onClick={onClose}><RollingLabel>Close</RollingLabel></button>
        </div>
      </div>
    </Modal>
  );
}
