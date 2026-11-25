import { useRef, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { useTheme } from "../context/ThemeContext";
import { useList } from "../hooks/useApi";
import { api } from "../services/api";
import { isAdmin } from "../utilities/roles";
import Loading from "../components/Loading";
import RollingLabel from "../components/RollingLabel";
import HoldToConfirmButton from "../components/HoldToConfirmButton";
import {
  DEFAULT_PALETTE, HEX_COLOUR, MIN_TEXT_CONTRAST, SHADE_STEPS, contrastRatio,
} from "../styles/palette";

const TEXT_STEPS = new Set([900, 800, 700]);

function emptyForm() {
  return {
    name: "",
    description: "",
    source_label: "",
    ...Object.fromEntries(
      SHADE_STEPS.map((step) => [`shade_${step}`, DEFAULT_PALETTE.shades[step]])
    ),
  };
}

function formFromPalette(palette) {
  return {
    name: palette.name || "",
    description: palette.description || "",
    source_label: palette.source_label || "",
    ...Object.fromEntries(
      SHADE_STEPS.map((step) => [`shade_${step}`, palette.shades?.[step] || ""])
    ),
  };
}

function Swatches({ shades, large = false }) {
  return (
    <span className="palette-swatches" aria-hidden="true">
      {SHADE_STEPS.map((step) => (
        <span
          key={step}
          className={`palette-swatch${large ? " large" : ""}`}
          style={{ backgroundColor: shades?.[step] || "#FFFFFF" }}
        />
      ))}
    </span>
  );
}

function validate(form) {
  if (!form.name.trim()) return "Give the palette a name.";
  for (const step of SHADE_STEPS) {
    const value = form[`shade_${step}`];
    if (!HEX_COLOUR.test(value || "")) {
      return `Ramp ${step} must be a six-digit hex colour such as #023E8A.`;
    }
  }
  for (const step of TEXT_STEPS) {
    const ratio = contrastRatio(form[`shade_${step}`], "#FFFFFF");
    if (ratio < MIN_TEXT_CONTRAST) {
      return `Ramp ${step} has only ${ratio.toFixed(2)}:1 contrast on white. Use a darker shade.`;
    }
  }
  return "";
}

// Platform and school administrators manage the global catalogue here. Palette
// colours are stored as data and applied by ThemeProvider; no palette-specific
// CSS or component code is added when a new palette is onboarded.
export default function ThemeManager({ embedded = false }) {
  const { user } = useAuth();
  const { push } = useToast();
  const { palette: active, refreshTheme } = useTheme();
  const { data: palettes, loading, error, reload } = useList("/theming/palettes/");
  const paletteFormRef = useRef(null);
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);
  const [formError, setFormError] = useState("");
  const [busy, setBusy] = useState(false);
  const [applyingId, setApplyingId] = useState(null);

  if (!isAdmin(user)) {
    return <div className="notice error" role="alert">Only platform and school administrators can manage the theme catalogue.</div>;
  }

  const customCount = (palettes || []).filter((palette) => !palette.is_builtin).length;

  function updateField(name, value) {
    setForm((current) => ({ ...current, [name]: value }));
    if (formError) setFormError("");
  }

  function resetForm() {
    setForm(emptyForm());
    setEditingId(null);
    setFormError("");
  }

  function startEdit(palette) {
    setForm(formFromPalette(palette));
    setEditingId(palette.id);
    setFormError("");
    window.scrollTo?.({ top: 0, behavior: "smooth" });
  }

  async function savePalette(event) {
    event.preventDefault();
    const problem = validate(form);
    if (problem) {
      setFormError(problem);
      return;
    }
    setBusy(true);
    setFormError("");
    try {
      const path = editingId ? `/theming/palettes/${editingId}/` : "/theming/palettes/";
      await (editingId
        ? api.patch(path, form)
        : api.post(path, form));
      push("Palette saved to the catalogue. Choose Apply to make it active.", "success");
      resetForm();
      reload();
      await refreshTheme();
    } catch (err) {
      setFormError(err.message || "The palette could not be saved.");
      push(err.message || "The palette could not be saved.", "error");
    } finally {
      setBusy(false);
    }
  }

  async function activate(palette) {
    if (palette.is_active || busy) return;
    setBusy(true);
    setApplyingId(palette.id);
    try {
      await api.post(`/theming/palettes/${palette.id}/activate/`, {});
      push(`${palette.name} is now active.`, "success");
      reload();
      await refreshTheme();
    } catch (err) {
      push(err.message, "error");
    } finally {
      setBusy(false);
      setApplyingId(null);
    }
  }

  async function remove(palette) {
    if (!window.confirm(`Delete ${palette.name}? This cannot be undone.`)) return;
    setBusy(true);
    try {
      await api.del(`/theming/palettes/${palette.id}/`);
      push("Palette deleted.", "success");
      reload();
    } catch (err) {
      push(err.message, "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className={embedded ? "appearance-embedded" : ""}>
      {!embedded && (
        <div className="page-head">
          <div>
            <div className="overline">Theme administration</div>
            <h1>Theme &amp; colours</h1>
            <p className="muted" style={{ marginTop: "0.2rem" }}>
              Choose the active palette or add your own. Changes apply to the public site,
              staff admin and learner portal.
            </p>
          </div>
          <button
            type="button"
            onClick={() => {
              const reduceMotion = typeof window.matchMedia === "function"
                ? window.matchMedia("(prefers-reduced-motion: reduce)").matches
                : false;
              paletteFormRef.current?.scrollIntoView({
                behavior: reduceMotion ? "auto" : "smooth",
                block: "start",
              });
            }}
          >
            <RollingLabel>Add your own palette</RollingLabel>
          </button>
        </div>
      )}

      {!embedded && (
        <div className="notice" style={{ marginBottom: "1rem" }}>
          One palette is active across the platform. To add your own, use the form below. Saved
          palettes appear in the catalogue with a Custom tag and stay there after sign out. Choose
          Apply when you want one to become active. Text shades must meet 4.5:1 contrast on white.
          {customCount > 0 && (
            <strong> {customCount} custom palette{customCount === 1 ? "" : "s"} saved.</strong>
          )}
        </div>
      )}
      {error && <div className="notice error" role="alert" style={{ marginBottom: "1rem" }}>{error}</div>}

      <div className="panel panel-pad" style={{ marginBottom: "1rem" }}>
        <div className="palette-active-card">
          <div>
            <div className="overline">Active palette</div>
            <h2 style={{ marginBottom: "0.2rem" }}>{active.name}</h2>
            <p className="muted" style={{ margin: 0 }}>
              {active.description || "No description supplied."}
            </p>
          </div>
          <div>
            <Swatches shades={active.shades} large />
            <div className="muted" style={{ fontSize: "0.75rem", marginTop: "0.3rem" }}>
              {active.sourceLabel || "Runtime catalogue"}
            </div>
          </div>
        </div>
      </div>

      <div className="panel" style={{ marginBottom: "1rem" }}>
        <div className="panel-pad" style={{ borderBottom: "1px solid var(--line)" }}>
          <h2 style={{ marginBottom: 0 }}>Palette catalogue</h2>
        </div>
        {loading ? <div className="panel-pad"><Loading /></div> : (
          <div style={{ overflowX: "auto" }}>
            <table className="data">
              <thead>
                <tr>
                  <th>Palette</th>
                  <th>Ramp</th>
                  <th>Source</th>
                  <th>Status</th>
                  <th className="theme-table-actions">Actions</th>
                </tr>
              </thead>
              <tbody>
                {(palettes || []).map((palette) => (
                  <tr key={palette.id}>
                    <td>
                      <strong>{palette.name}</strong>
                      {!palette.is_builtin && <span className="tag info" style={{ marginLeft: "0.4rem" }}>Custom</span>}
                    </td>
                    <td><Swatches shades={palette.shades} /></td>
                    <td className="muted">{palette.source_label || "—"}</td>
                    <td>{palette.is_active ? <span className="tag good">Active</span> : <span className="tag">Available</span>}</td>
                    <td>
                      <div className="row-actions">
                        <button
                          className="small"
                          disabled={busy || palette.is_active}
                          aria-label={`${applyingId === palette.id ? "Applying" : palette.is_active ? "Applied" : "Apply"} ${palette.name || "palette"} palette`}
                          onClick={() => activate(palette)}
                        >
                          {applyingId === palette.id ? "Applying…" : palette.is_active ? <RollingLabel>Applied</RollingLabel> : <RollingLabel>Apply</RollingLabel>}
                        </button>
                        <button
                          className="secondary small"
                          disabled={busy}
                          aria-label={`Edit ${palette.name || "palette"} palette`}
                          onClick={() => startEdit(palette)}
                        >
                          <RollingLabel>Edit</RollingLabel>
                        </button>
                        {!palette.is_builtin && !palette.is_active && (
                          <HoldToConfirmButton
                            className="ghost small danger"
                            disabled={busy}
                            aria-label={`Delete ${palette.name || "palette"} palette`}
                            onConfirm={() => remove(palette)}
                          >
                            Delete
                          </HoldToConfirmButton>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <form ref={paletteFormRef} className="panel panel-pad" onSubmit={savePalette}>
        <div className="overline">{editingId ? "Edit palette" : "Add your own palette"}</div>
        <h2>{editingId ? "Update palette colours" : "Add your own colour set"}</h2>
        <p className="muted">
          Paste nine six-digit hex values, darkest first. The three darkest steps are used for
          text and must pass the contrast check. Saving adds the palette to the catalogue shown
          above; nothing is active until you choose Apply.
        </p>
        {formError && <div className="notice error" role="alert" style={{ marginBottom: "0.8rem" }}>{formError}</div>}

        <div className="form-grid">
          <div>
            <label htmlFor="palette-name">Palette name</label>
            <input
              id="palette-name"
              value={form.name}
              required
              onChange={(event) => updateField("name", event.target.value)}
            />
          </div>
          <div>
            <label htmlFor="palette-source">Source or reference</label>
            <input
              id="palette-source"
              value={form.source_label}
              placeholder="For example, colors.png"
              onChange={(event) => updateField("source_label", event.target.value)}
            />
          </div>
          <div className="full">
            <label htmlFor="palette-description">Description</label>
            <textarea
              id="palette-description"
              value={form.description}
              rows={2}
              onChange={(event) => updateField("description", event.target.value)}
            />
          </div>

          {SHADE_STEPS.map((step) => {
            const field = `shade_${step}`;
            const value = form[field];
            const valid = HEX_COLOUR.test(value || "");
            const ratio = valid ? contrastRatio(value, "#FFFFFF") : null;
            const fails = TEXT_STEPS.has(step) && ratio !== null && ratio < MIN_TEXT_CONTRAST;
            return (
              <div key={step}>
                <label htmlFor={`shade-${step}`}>Ramp {step}{TEXT_STEPS.has(step) ? " (text)" : ""}</label>
                <div className="theme-form-shade">
                  <span
                    className="theme-form-swatch"
                    style={{ backgroundColor: valid ? value : "transparent" }}
                    aria-hidden="true"
                  />
                  <input
                    id={`shade-${step}`}
                    type="text"
                    value={value}
                    spellCheck="false"
                    onChange={(event) => updateField(field, event.target.value)}
                  />
                </div>
                {TEXT_STEPS.has(step) && (
                  <div className={`theme-contrast${fails ? " fail" : ""}`}>
                    {ratio === null ? "Enter a hex colour" : `${ratio.toFixed(2)}:1 on white`}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <div className="form-actions">
          {editingId && <button type="button" className="ghost" onClick={resetForm}><RollingLabel>Cancel edit</RollingLabel></button>}
          <button type="submit" disabled={busy}>
            {busy ? "Saving…" : editingId ? <RollingLabel>Save palette</RollingLabel> : <RollingLabel>Add palette</RollingLabel>}
          </button>
        </div>
      </form>
    </section>
  );
}
