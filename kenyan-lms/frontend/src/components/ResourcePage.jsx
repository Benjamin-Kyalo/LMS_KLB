import { useEffect, useState } from "react";
import { useList } from "../hooks/useApi";
import useTableControls from "../hooks/useTableControls";
import { api, listAll } from "../services/api";
import { useToast } from "../context/ToastContext";
import DataTable from "./DataTable";
import Modal from "./Modal";
import FormField from "./FormField";
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
    if (row && row[field.name] !== undefined && row[field.name] !== null) {
      return field.type === "json" ? JSON.stringify(row[field.name]) : row[field.name];
    }
    if (typeof field.default === "function") return field.default();
    return field.default ?? (field.type === "checkbox" ? false : "");
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
      const payload = { ...form };
      for (const field of fields) {
        if (field.type === "json" && payload[field.name]) {
          try { payload[field.name] = JSON.parse(payload[field.name]); }
          catch { throw new Error(`Invalid JSON in ${field.label}.`); }
        }
      }
      const result = editing
        ? await api.patch(`${endpoint}${editing.id}/`, payload)
        : await api.post(endpoint, payload);
      if (result && result.queued) push("Saved offline — it will sync when connected.", "info");
      else push(`${title}: ${editing ? "updated" : "created"}.`, "success");
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
      <button className="ghost small" onClick={() => setDetail(row)}>View</button>
      {canEdit && <button className="ghost small" onClick={() => startEdit(row)}>Edit</button>}
      {canDelete && <button className="ghost small danger" onClick={() => remove(row)}>Delete</button>}
    </div>
  );
  const allColumns = [...columns, { key: "_actions", label: "Actions", render: rowActions }];

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">{overline}</div>
          <h1>{title}</h1>
        </div>
        <div className="actions">
          {canCreate && <button onClick={startCreate}>New</button>}
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
        emptyAction={!controls.query && canCreate ? <button onClick={startCreate}>Create the first {title.toLowerCase().replace(/s$/, "")}</button> : null}
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
            {canEdit && <button type="button" onClick={() => startEdit(detail)}>Edit</button>}
            {canDelete && <button type="button" className="ghost danger" onClick={() => remove(detail)}>Delete</button>}
            <button type="button" className="ghost" onClick={() => setDetail(null)}>Close</button>
          </div>
        </Modal>
      )}

      {open && (
        <Modal title={`${editing ? "Edit" : "New"} ${title.toLowerCase().replace(/s$/, "")}`} onClose={() => { setOpen(false); setEditing(null); }}>
          <form onSubmit={save}>
            {formError && <div className="notice error" style={{ marginBottom: "0.75rem" }}>{formError}</div>}
            <div className="form-grid">
              {fields.map((field) => {
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
                    ) : (
                      <input type={field.type || "text"} value={form[field.name] ?? ""} onChange={(e) => setForm({ ...form, [field.name]: e.target.value })} required={field.required} />
                    )}
                  </FormField>
                );
              })}
            </div>
            <div className="form-actions">
              <button type="button" className="ghost" onClick={() => { setOpen(false); setEditing(null); }}>Cancel</button>
              <button type="submit" disabled={saving}>{saving ? "Saving…" : editing ? "Save changes" : "Save"}</button>
            </div>
          </form>
        </Modal>
      )}
    </section>
  );
}
