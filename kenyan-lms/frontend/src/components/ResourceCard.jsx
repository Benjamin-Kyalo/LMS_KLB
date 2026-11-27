import { useState } from "react";
import { BookOpen } from "lucide-react";
import RollingLabel from "./RollingLabel";

function first(...values) {
  return values.find((value) => value !== null && value !== undefined && value !== "") || "";
}

export default function ResourceCard({ resource, onSelect }) {
  const level = first(resource.education_level_name, resource.level_name);
  const area = first(resource.learning_area_name, resource.collection_name);
  const availability = resource.offline_available ? "Downloadable" : "Online";
  const [busy, setBusy] = useState(false);
  const [thumbFailed, setThumbFailed] = useState(false);
  const thumbnail = resource.thumbnail_url && !thumbFailed ? resource.thumbnail_url : "";
  const resourceName = resource.title || "resource";
  const viewLabel = `View resource: ${resourceName}`;
  const busyLabel = `Preparing resource: ${resourceName}`;

  async function view() {
    setBusy(true);
    try { await onSelect(resource); }
    finally { setBusy(false); }
  }

  return (
    <article className="resource-card panel">
      <div className="resource-card-media">
        {thumbnail ? (
          <img
            src={thumbnail}
            alt={`Thumbnail for ${resource.title}`}
            width="640"
            height="360"
            loading="lazy"
            decoding="async"
            onError={() => setThumbFailed(true)}
          />
        ) : (
          <div className="resource-card-media-fallback" aria-hidden="true">
            <BookOpen size={30} strokeWidth={1.5} />
            <span>{resource.resource_type || "Resource"}</span>
          </div>
        )}
      </div>
      <div className="resource-card-body">
        <div className="resource-card-tags">
          <span className="tag info">{resource.resource_type || "Resource"}</span>
          <span className="tag">{availability}</span>
        </div>
        <h3>{resource.title}</h3>
        {(level || area) && (
          <p className="muted resource-card-context">{[level, area].filter(Boolean).join(" · ")}</p>
        )}
        {resource.description && <p className="resource-card-copy">{resource.description}</p>}
      </div>
      <div className="resource-card-actions">
        <button
          type="button"
          className="secondary small"
          onClick={view}
          aria-label={busy ? busyLabel : viewLabel}
          aria-busy={busy}
          disabled={busy}
        >
          <RollingLabel>{busy ? "Preparing resource" : "View resource"}</RollingLabel>
        </button>
      </div>
    </article>
  );
}
