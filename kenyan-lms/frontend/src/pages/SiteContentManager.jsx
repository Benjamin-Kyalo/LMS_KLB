import { useEffect, useRef, useState } from "react";
import { ImageOff } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useSiteContent } from "../context/SiteContentContext";
import { useToast } from "../context/ToastContext";
import { SITE_CONTENT_GROUPS, getIn, setIn } from "../config/publicSite";
import { api } from "../services/api";
import { HEX_COLOUR } from "../styles/palette";
import { firstStyleError } from "../styles/sectionStyles";
import { isAdmin } from "../utilities/roles";
import HoldToConfirmButton from "../components/HoldToConfirmButton";
import RollingLabel from "../components/RollingLabel";

function clone(value) {
  return JSON.parse(JSON.stringify(value || {}));
}

function toLines(value) {
  return Array.isArray(value) ? value.join("\n") : "";
}

function fromLines(value) {
  return String(value || "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
}

const PHOTO_TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);
const PHOTO_EXTENSIONS = new Set(["jpg", "jpeg", "png", "webp"]);
const PHOTO_MAX_BYTES = 5 * 1024 * 1024;
const PHOTO_MIN_WIDTH = 640;
const PHOTO_MIN_HEIGHT = 360;

function basicPhotoError(file) {
  const match = /\.([^.]+)$/.exec(file.name || "");
  const extension = match ? match[1].toLowerCase() : "";
  const type = (file.type || "").toLowerCase();
  if (!PHOTO_EXTENSIONS.has(extension) || (type && !PHOTO_TYPES.has(type))) {
    return "Use a JPG, PNG or WebP photo.";
  }
  if (file.size > PHOTO_MAX_BYTES) {
    return "The photo must be 5 MB or smaller.";
  }
  return "";
}

async function validatePhoto(file) {
  const basic = basicPhotoError(file);
  if (basic) return basic;
  if (typeof createImageBitmap !== "function") return "";
  let bitmap;
  try {
    bitmap = await createImageBitmap(file);
  } catch {
    return "The file is not a readable image.";
  }
  try {
    if (bitmap.width < PHOTO_MIN_WIDTH || bitmap.height < PHOTO_MIN_HEIGHT) {
      return `Use a photo at least ${PHOTO_MIN_WIDTH}×${PHOTO_MIN_HEIGHT} pixels.`;
    }
    return "";
  } finally {
    if (typeof bitmap.close === "function") bitmap.close();
  }
}

function Label({ field }) {
  return (
    <label htmlFor={`site-${field.path.replaceAll(".", "-")}`}>
      {field.label}
      {field.hint && <span className="site-content-hint">{field.hint}</span>}
    </label>
  );
}

function ObjectListField({ field, value, onChange }) {
  const rows = Array.isArray(value) ? value : [];
  const updateRow = (index, key, nextValue) => {
    const next = rows.map((row, rowIndex) => (
      rowIndex === index ? { ...row, [key]: nextValue } : row
    ));
    onChange(field.path, next);
  };
  const addRow = () => {
    const row = Object.fromEntries((field.itemFields || []).map((item) => [
      item.key,
      item.type === "lines" ? [] : "",
    ]));
    onChange(field.path, [...rows, row]);
  };
  const removeRow = (index) => {
    onChange(field.path, rows.filter((_, rowIndex) => rowIndex !== index));
  };

  return (
    <div>
      <Label field={field} />
      {rows.map((row, index) => (
        <div className="site-content-row" key={`${field.path}-${index}`}>
          <div className="site-content-row-head">
            <span>Item {index + 1}</span>
            <button
              type="button"
              className="ghost small danger"
              aria-label={`Remove item ${index + 1} from ${field.label}`}
              onClick={() => removeRow(index)}
            >
              Remove
            </button>
          </div>
          <div className="site-content-object-grid">
            {(field.itemFields || []).map((item) => {
              const id = `site-${field.path.replaceAll(".", "-")}-${index}-${item.key}`;
              return (
                <div key={item.key}>
                  <label htmlFor={id}>{item.label}</label>
                  {item.type === "textarea" || item.type === "lines" ? (
                    <textarea
                      id={id}
                      rows={item.type === "lines" ? 4 : 2}
                      value={item.type === "lines" ? toLines(row[item.key]) : row[item.key] || ""}
                      onChange={(event) => updateRow(
                        index,
                        item.key,
                        item.type === "lines" ? fromLines(event.target.value) : event.target.value,
                      )}
                    />
                  ) : (
                    <input
                      id={id}
                      type="text"
                      value={row[item.key] || ""}
                      disabled={Boolean(item.readOnly)}
                      onChange={(event) => updateRow(index, item.key, event.target.value)}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}
      <button type="button" className="secondary small" onClick={addRow}>
        <RollingLabel>Add an item</RollingLabel>
      </button>
    </div>
  );
}

function PhotoCard({ field, value, onUpload, onRemove, onReset, busySlot, uploaded }) {
  const id = `site-${field.path.replaceAll(".", "-")}`;
  const [file, setFile] = useState(null);
  const [fileError, setFileError] = useState("");
  const [checking, setChecking] = useState(false);
  const checkId = useRef(0);
  const busy = busySlot === field.slot;

  useEffect(() => () => { checkId.current += 1; }, []);

  async function choose(event) {
    const chosen = event.target.files?.[0] || null;
    const current = ++checkId.current;
    const basic = chosen ? basicPhotoError(chosen) : "";
    setFile(chosen);
    setFileError(basic);
    if (!chosen || basic || typeof createImageBitmap !== "function") return;
    setChecking(true);
    const error = await validatePhoto(chosen);
    if (current === checkId.current) {
      setFileError(error);
      setChecking(false);
    }
  }

  return (
    <div className="photo-card panel">
      <div className="photo-card-preview">
        {value ? (
          <img src={value} alt="" width="640" height="360" loading="lazy" decoding="async" />
        ) : (
          <div className="photo-card-empty" aria-hidden="true">
            <ImageOff size={28} strokeWidth={1.5} />
            <span>No photo set</span>
          </div>
        )}
      </div>
      <div className="photo-card-body">
        <h3><label htmlFor={`${id}-file`}>{field.label}</label></h3>
        {field.hint && <p className="muted">{field.hint}</p>}
        <input
          id={`${id}-file`}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          aria-label={`Choose a new photo for ${field.label}`}
          aria-invalid={Boolean(fileError) || undefined}
          aria-describedby={fileError ? `${id}-file-error` : undefined}
          onChange={choose}
        />
        <div className="photo-card-actions">
          <button
            type="button"
            className="secondary small"
            disabled={!file || busy || checking || Boolean(fileError)}
            aria-busy={busy || checking || undefined}
            onClick={() => onUpload(field, file)}
          >
            {uploaded ? "Photo published ✓" : busy ? "Publishing…" : checking ? "Checking…" : <RollingLabel>{value ? "Replace photo" : "Upload photo"}</RollingLabel>}
          </button>
          <button
            type="button"
            className="ghost small"
            disabled={busy}
            aria-label={`Restore the default ${field.label.toLowerCase()}`}
            onClick={() => onReset(field)}
          >
            <RollingLabel>Restore default</RollingLabel>
          </button>
          <HoldToConfirmButton
            className="ghost small danger"
            disabled={!value || busy}
            aria-label={`Remove ${field.label.toLowerCase()}`}
            onConfirm={() => onRemove(field)}
          >
            Remove
          </HoldToConfirmButton>
        </div>
        {fileError && (
          <small id={`${id}-file-error`} className="site-content-error" role="alert">
            {fileError} Choose another file to continue.
          </small>
        )}
        <small className="site-content-hint">
          JPG, PNG or WebP, at least 640×360 px and up to 5 MB. Uploading publishes the photo immediately.
        </small>
        <small className="photo-card-current" title={value || "None"}>
          Current: {value || "none"}
        </small>
      </div>
    </div>
  );
}

function ColourField({ field, value, onChange }) {
  const id = `site-${field.path.replaceAll(".", "-")}`;
  const colour = HEX_COLOUR.test(value || "") ? value : "#FFFFFF";
  return (
    <div>
      <Label field={field} />
      <div className="style-colour-input">
        <input
          type="color"
          value={colour}
          aria-label={`Pick ${field.label.toLowerCase()}`}
          onChange={(event) => onChange(field.path, event.target.value.toUpperCase())}
        />
        <input
          id={id}
          type="text"
          value={value || ""}
          placeholder="Inherit"
          onChange={(event) => onChange(field.path, event.target.value.trim())}
        />
        <button
          type="button"
          className="ghost small"
          aria-label={`Inherit ${field.label.toLowerCase()}`}
          onClick={() => onChange(field.path, "")}
        >
          <RollingLabel>Inherit</RollingLabel>
        </button>
      </div>
    </div>
  );
}

function ChoiceField({ field, value, onChange }) {
  const id = `site-${field.path.replaceAll(".", "-")}`;
  return (
    <div>
      <Label field={field} />
      <select
        id={id}
        value={value || ""}
        onChange={(event) => onChange(field.path, event.target.value)}
      >
        {(field.choices || []).map((choice) => (
          <option key={choice.value} value={choice.value}>{choice.label}</option>
        ))}
      </select>
    </div>
  );
}

function Field({ field, value, onChange }) {
  const id = `site-${field.path.replaceAll(".", "-")}`;
  if (field.type === "objectList") {
    return <ObjectListField field={field} value={value} onChange={onChange} />;
  }
  if (field.type === "colour") {
    return <ColourField field={field} value={value} onChange={onChange} />;
  }
  if (field.type === "choice") {
    return <ChoiceField field={field} value={value} onChange={onChange} />;
  }
  return (
    <div>
      <Label field={field} />
      {field.type === "textarea" || field.type === "lines" ? (
        <textarea
          id={id}
          rows={field.type === "lines" ? 6 : 3}
          value={field.type === "lines" ? toLines(value) : value || ""}
          onChange={(event) => onChange(
            field.path,
            field.type === "lines" ? fromLines(event.target.value) : event.target.value,
          )}
        />
      ) : (
        <input
          id={id}
          type="text"
          value={value || ""}
          onChange={(event) => onChange(field.path, event.target.value)}
        />
      )}
    </div>
  );
}

export default function SiteContentManager({
  embedded = false,
  initialGroup = null,
  visibleGroupIds = null,
  groups: suppliedGroups = null,
}) {
  const { user } = useAuth();
  const { content, refreshSiteContent } = useSiteContent();
  const { push } = useToast();
  const groups = suppliedGroups
    || (visibleGroupIds
      ? SITE_CONTENT_GROUPS.filter((item) => visibleGroupIds.includes(item.id))
      : SITE_CONTENT_GROUPS);
  const [draft, setDraft] = useState(() => clone(content));
  const [edited, setEdited] = useState(false);
  const [groupId, setGroupId] = useState(initialGroup || groups[0]?.id || "");
  const [busy, setBusy] = useState(false);
  const [busySlot, setBusySlot] = useState("");
  const [uploadedPath, setUploadedPath] = useState("");
  const contentKey = JSON.stringify(content);

  useEffect(() => { refreshSiteContent(); }, [refreshSiteContent]);
  useEffect(() => {
    if (!edited) setDraft(JSON.parse(contentKey));
  }, [contentKey, edited]);

  const canEdit = isAdmin(user);
  if (!canEdit) {
    return (
      <div className="notice error" role="alert">
        Only administrators can edit site wording and appearance.
      </div>
    );
  }

  const group = groups.find((item) => item.id === groupId) || groups[0];
  const styleGroup = Boolean(group?.fields?.some((field) => (
    field.type === "colour" || field.type === "choice"
  )));

  function change(path, value) {
    setEdited(true);
    setDraft((current) => setIn(current, path, value));
  }

  function reset() {
    setDraft(clone(content));
    setEdited(false);
  }

  async function applyPhoto(field, action, label, success, markPublished = false) {
    setBusySlot(field.slot);
    setUploadedPath("");
    try {
      const result = await action();
      const refreshed = await refreshSiteContent();
      setDraft(clone(refreshed || result?.content || content));
      setEdited(false);
      push(`${label} ${success}.`, "success");
      if (markPublished) {
        setUploadedPath(field.path);
        setTimeout(() => setUploadedPath(""), 1400);
      }
    } catch (err) {
      push(err.message || `${label} could not be updated.`, "error");
    } finally {
      setBusySlot("");
    }
  }

  function uploadPhoto(field, file) {
    const form = new FormData();
    form.append("image", file);
    form.append("slot", field.slot || "hero");
    return applyPhoto(
      field,
      () => api.upload("/theming/site-content/image/", form, "POST"),
      field.label,
      "uploaded and published",
      true,
    );
  }

  function removePhoto(field) {
    return applyPhoto(
      field,
      () => api.del(`/theming/site-content/image/${field.slot}/`),
      field.label,
      "removed",
    );
  }

  function resetPhoto(field) {
    return applyPhoto(
      field,
      () => api.post(`/theming/site-content/image/${field.slot}/reset/`, {}),
      field.label,
      "restored to the default",
    );
  }

  async function save(event) {
    event.preventDefault();
    const styleError = firstStyleError(draft.styles);
    if (styleError) {
      push(styleError, "error");
      return;
    }
    setBusy(true);
    try {
      await api.patch("/theming/site-content/", { content: draft });
      const saved = await refreshSiteContent();
      setDraft(clone(saved || draft));
      setEdited(false);
      push("Site content saved. Public pages now use the new settings.", "success");
    } catch (err) {
      push(err.message || "The site content could not be saved.", "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className={embedded ? "appearance-embedded" : ""}>
      {!embedded && (
        <div className="page-head view-enter">
          <div>
            <div className="overline">Public site content</div>
            <h1>Site words and navigation</h1>
            <p className="muted" style={{ marginTop: "0.2rem" }}>
              Edit the header, footer, homepage, library and sign in wording here. Save once and
              the same words appear across the public site, staff area and learner portal.
            </p>
          </div>
        </div>
      )}

      {!embedded && (
        <div className="notice" style={{ marginBottom: "1rem" }}>
          Changes are stored with the site data at <code>/api/theming/site-content/</code>. They stay
          in place after sign out, and a saved copy is used until the next update arrives.
        </div>
      )}

      <form onSubmit={save}>
        <div className="site-content-layout">
          <nav className="site-content-nav" aria-label="Site content sections">
            {groups.map((item) => (
              <button
                type="button"
                key={item.id}
                className={`site-content-group-btn${item.id === group.id ? " is-selected" : ""}`}
                aria-pressed={item.id === group.id}
                onClick={() => setGroupId(item.id)}
              >
                {item.title}
              </button>
            ))}
          </nav>

          <div className="panel panel-pad">
            <h2>{group.title}</h2>
            <p className="muted">{group.description}</p>
            {group.id === "photos" ? (
              <div className="photo-grid">
                {(group.fields || []).map((field) => (
                  <PhotoCard
                    key={field.path}
                    field={field}
                    value={getIn(draft, field.path)}
                    onUpload={uploadPhoto}
                    onRemove={removePhoto}
                    onReset={resetPhoto}
                    busySlot={busySlot}
                    uploaded={uploadedPath === field.path}
                  />
                ))}
              </div>
            ) : (
              <div className={styleGroup ? "site-content-fields style-field-grid" : "site-content-fields"}>
                {(group.fields || []).map((field) => (
                  <Field
                    key={field.path}
                    field={field}
                    value={getIn(draft, field.path)}
                    onChange={change}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {group.id !== "photos" && (
          <div className="site-content-actions">
            <div className="form-actions">
              <button
                type="button"
                className="ghost"
                disabled={busy || !edited}
                onClick={reset}
              >
                <RollingLabel>Undo changes</RollingLabel>
              </button>
              <button type="submit" disabled={busy || !edited} aria-busy={busy || undefined}>
                {busy ? "Saving…" : <RollingLabel>Save site content</RollingLabel>}
              </button>
            </div>
          </div>
        )}
      </form>
    </section>
  );
}
