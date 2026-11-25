import { useEffect, useState } from "react";
import { useList } from "../hooks/useApi";
import useTableControls from "../hooks/useTableControls";
import { api, listAll } from "../services/api";
import { useToast } from "../context/ToastContext";
import DataTable from "./DataTable";
import Modal from "./Modal";
import FormField from "./FormField";
import RollingLabel from "./RollingLabel";
import HoldToConfirmButton from "./HoldToConfirmButton";
import { TablePagination, TableToolbar } from "./TableTools";

// A reusable list + create + detail/edit + delete page for simple resources.
// columns: [{key,label,render?}]
// fields: [{name,label,type,options?,optionsEndpoint?,labelKey?,valueKey?,required?,full?,hint?}]
export default function ResourcePage({
  title, overline, endpoint, columns, fields, emptyHint,
  canCreate = true, canEdit = true, canDelete = true,
}) {
  const { data, loading, error, reload } = useList(endpoint);
  const { push } = useToast();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [detail, setDetail] = useState(null);
  const [form, setForm] = useState({});
  const [dynamicOptions, setDynamicOptions] = useState({});
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState(null);
  const controls = useTableControls(data);

  useEffect(() => {
    let current = true;
    fields.filter((field) => field.optionsEndpoint).forEach(async (field) => {
      try {
        const rows = await listAll(field.optionsEndpoint);
        if (!current) return;
        setDynamicOptions((previous) => ({
          ...previous,
          [field.name]: rows.map((row) => ({
            value: String(row[field.valueKey || "id"]),
            label: String(row[field.labelKey || "name"]),
          })),
        }));
      } catch {
        // The form still renders; the field will show the choose prompt.
      }
    });
    return () => { current = false; };
  }, [fields]);

  function initialValue(field, row) {
    // A browser file input cannot be pre-filled; an existing file is shown by
    // the detail view and left untouched unless a new file is chosen.
    if (field.type === "file") return null;
    if (row && row[field.name] !== undefined && row[field.name] !== null) {
      return field.type === "json" ? JSON.stringify(row[field.name]) : row[field.name];
    }
    if (typeof field.default === "function") return field.default();
    return field.default ?? (field.type === "checkbox" ? false : "");
  }

  function visibleFields() {
    return fields.filter((field) => !field.showWhen || field.showWhen(form));
  }

  function startCreate() {
    setEditing(null);
    setForm(Object.fromEntries(fields.map((field) => [field.name, initialValue(field)])));
    setFormError(null);
    setOpen(true);
  }

  function startEdit(row) {
    setEditing(row);
    setForm(Object.fromEntries(fields.map((field) => [field.name, initialValue(field, row)])));
    setFormError(null);
    setDetail(null);
    setOpen(true);
  }

  async function save(e) {
    e.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      const active = visibleFields();
      const payload = {};
      for (const field of active) {
        if (field.type === "file") continue;
        let value = form[field.name];
        if (field.type === "json" && value) {
          try { value = JSON.parse(value); }
          catch { throw new Error(`Invalid JSON in ${field.label}.`); }
        }
        if (value !== undefined && value !== null && value !== "") {
          payload[field.name] = value;
        }
      }

      const uploadFields = active.filter(
        (field) => field.type === "file" && form[field.name] instanceof File,
      );
      if (uploadFields.length > 0) {
        // Files go through the direct upload path.
        const formData = new FormData();
        Object.entries(payload).forEach(([key, value]) => {
          formData.append(key, typeof value === "object" ? JSON.stringify(value) : String(value));
        });
        uploadFields.forEach((field) => formData.append(field.name, form[field.name]));
        if (editing) {
          await api.upload(`${endpoint}${editing.id}/`, formData, "PATCH");
        } else {
          await api.upload(endpoint, formData, "POST");
        }
      } else if (editing) {
        await api.patch(`${endpoint}${editing.id}/`, payload);
      } else {
        await api.post(endpoint, payload);
      }
      push(`${title}: ${editing ? "updated" : "created"}.`, "success");
      setOpen(false);
      setEditing(null);
      reload();
    } catch (err) {
      setFormError(err.details ? JSON.stringify(err.details) : err.message);
    } finally {
      setSaving(false);
    }
  }

  async function remove(row) {
    if (!window.confirm(`Delete this ${title.toLowerCase()}? This cannot be undone.`)) return;
    try {
      await api.del(`${endpoint}${row.id}/`);
      push("Deleted.", "success");
      if (detail?.id === row.id) setDetail(null);
      reload();
    } catch (err) {
      push(err.message, "error");
    }
  }

  function displayValue(value) {
    if (value === null || value === undefined || value === "") return "—";
    if (typeof value === "object") return JSON.stringify(value);
    return String(value);
  }

  const rowActions = (row) => (
    <div className="row-actions">
      <button className="ghost small" aria-label={`View ${row.name || row.title || row.username || "record"}`} onClick={() => setDetail(row)}><RollingLabel>View</RollingLabel></button>
      {canEdit && <button className="ghost small" aria-label={`Edit ${row.name || row.title || row.username || "record"}`} onClick={() => startEdit(row)}><RollingLabel>Edit</RollingLabel></button>}
      {canDelete && (
        <HoldToConfirmButton
          className="ghost small danger"
          aria-label={`Delete ${row.name || row.title || row.username || "record"}`}
          onConfirm={() => remove(row)}
        >
          Delete
        </HoldToConfirmButton>
      )}
    </div>
  );
  const allColumns = [...columns, { key: "_actions", label: "Actions", render: rowActions }];
  const activeFields = visibleFields();
  const fieldSections = activeFields.reduce((sections, field) => {
    const name = field.section || "Details";
    const existing = sections.find((section) => section.name === name);
    if (existing) existing.fields.push(field);
    else sections.push({ name, fields: [field] });
    return sections;
  }, []);

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">{overline}</div>
          <h1>{title}</h1>
        </div>
        <div className="actions">
          {canCreate && <button onClick={startCreate}><RollingLabel>New</RollingLabel></button>}
        </div>
      </div>

      <TableToolbar title={title} controls={controls} onRefresh={reload} />

      <DataTable
        columns={allColumns}
        rows={controls.visibleRows}
        loading={loading}
        error={error}
        emptyTitle={controls.query ? "No matching records" : `No ${title.toLowerCase()} yet`}
        emptyHint={controls.query ? "Try a different search term." : emptyHint}
        emptyAction={!controls.query && canCreate ? <button onClick={startCreate}><RollingLabel>Create the first {title.toLowerCase().replace(/s$/, "")}</RollingLabel></button> : null}
      />

      {!loading && !error && <TablePagination controls={controls} />}

      {detail && (
        <Modal title={`${title} details`} onClose={() => setDetail(null)}>
          <dl className="detail-list">
            {columns.map((column) => (
              <div key={column.key}>
                <dt>{column.label || "Field"}</dt>
                <dd>{displayValue(detail[column.key])}</dd>
              </div>
            ))}
          </dl>
          <div className="form-actions">
            {canEdit && <button type="button" onClick={() => startEdit(detail)}><RollingLabel>Edit</RollingLabel></button>}
            {canDelete && (
              <HoldToConfirmButton
                type="button"
                className="ghost danger"
                aria-label={`Delete ${detail.name || detail.title || detail.username || "record"}`}
                onConfirm={() => remove(detail)}
              >
                Delete
              </HoldToConfirmButton>
            )}
            <button type="button" className="ghost" onClick={() => setDetail(null)}><RollingLabel>Close</RollingLabel></button>
          </div>
        </Modal>
      )}

      {open && (
        <Modal title={`${editing ? "Edit" : "New"} ${title.toLowerCase().replace(/s$/, "")}`} onClose={() => { setOpen(false); setEditing(null); }}>
          <form onSubmit={save}>
            {formError && <div className="notice error" role="alert" style={{ marginBottom: "0.75rem" }}>{formError}</div>}
            {fieldSections.map((section) => (
              <fieldset className="form-section" key={section.name}>
                <legend>{section.name}</legend>
                <div className="form-grid">
                  {section.fields.map((field) => {
                    const options = field.optionsEndpoint ? (dynamicOptions[field.name] || []) : (field.options || []);
                    return (
                      <FormField key={field.name} label={field.label} hint={field.hint} full={field.full}>
                        {field.type === "select" ? (
                          <select value={form[field.name] ?? ""} onChange={(e) => setForm({ ...form, [field.name]: e.target.value })}>
                            <option value="">— choose —</option>
                            {options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                          </select>
                        ) : field.type === "textarea" || field.type === "json" ? (
                          <textarea rows={field.type === "json" ? 4 : 3} value={form[field.name] ?? ""} placeholder={field.type === "json" ? '["option A", "option B"]' : undefined} onChange={(e) => setForm({ ...form, [field.name]: e.target.value })} />
                        ) : field.type === "checkbox" ? (
                          <input type="checkbox" checked={Boolean(form[field.name])} onChange={(e) => setForm({ ...form, [field.name]: e.target.checked })} style={{ width: "auto" }} />
                        ) : field.type === "file" ? (
                          <input type="file" accept={field.accept} onChange={(e) => setForm({ ...form, [field.name]: e.target.files?.[0] || null })} />
                        ) : (
                          <input type={field.type || "text"} value={form[field.name] ?? ""} onChange={(e) => setForm({ ...form, [field.name]: e.target.value })} required={field.required} />
                        )}
                      </FormField>
                    );
                  })}
                </div>
              </fieldset>
            ))}
            <div className="form-actions">
              <button type="button" className="ghost" onClick={() => { setOpen(false); setEditing(null); }}><RollingLabel>Cancel</RollingLabel></button>
              <button type="submit" disabled={saving}>{saving ? "Saving…" : editing ? <RollingLabel>Save changes</RollingLabel> : <RollingLabel>Save</RollingLabel>}</button>
            </div>
          </form>
        </Modal>
      )}
    </section>
  );
}
