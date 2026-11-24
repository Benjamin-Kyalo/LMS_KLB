import { useState } from "react";
import { Link } from "react-router-dom";
import { useList, useResource } from "../hooks/useApi";
import { api } from "../services/api";
import { useToast } from "../context/ToastContext";
import DataTable from "../components/DataTable";
import FormField from "../components/FormField";
import { statusTag } from "../utilities/format";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

// Local export staging. Nothing is transmitted to KEMIS from this page.
export default function KemisExports() {
  const { push } = useToast();
  const datasets = useResource("/kemis/exports/datasets/");
  const { data, loading, error, reload } = useList("/kemis/exports/");
  const [dataset, setDataset] = useState("LEARNERS");
  const [format, setFormat] = useState("CSV");
  const [filters, setFilters] = useState("{}");
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);

  const options = datasets.data?.datasets || datasets.data || [];

  async function generate(e) {
    e.preventDefault();
    setBusy(true);
    try {
      let parsed = {};
      if (filters.trim()) {
        parsed = JSON.parse(filters);
        if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
          throw new Error("Filters must be a JSON object.");
        }
      }
      const response = await api.post("/kemis/exports/generate/", { dataset, format, filters: parsed });
      setResult(response);
      push("Export generated and stored locally.", "success");
      reload();
    } catch (err) {
      push(err.message, "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">Government reporting</div>
          <h1>KEMIS exports</h1>
        </div>
        <div className="actions">
          <Link className="button secondary" to="/admin/kemis/mappings">Field mappings</Link>
        </div>
      </div>

      <div className="notice" style={{ marginBottom: "1rem" }}>
        Local staging only. Column names are a working approximation and must be checked against
        the current official KEMIS template before any submission. Nothing is sent to KEMIS and
        no credentials are stored here.
      </div>

      <div className="panel panel-pad">
        <h2 style={{ marginTop: 0 }}>Generate an export</h2>
        <form onSubmit={generate}>
          <div className="form-grid">
            <FormField label="Dataset">
              <select value={dataset} onChange={(e) => setDataset(e.target.value)}>
                {(Array.isArray(options) ? options : []).map((item) => {
                  const value = typeof item === "string" ? item : (item.key || item.dataset || item.value);
                  const label = typeof item === "string" ? item.replace(/_/g, " ") : (item.label || value);
                  return <option key={value} value={value}>{label}</option>;
                })}
                {!options.length && <option value="LEARNERS">Learners</option>}
              </select>
            </FormField>
            <FormField label="Format">
              <select value={format} onChange={(e) => setFormat(e.target.value)}>
                <option value="CSV">CSV</option>
                <option value="JSON">JSON</option>
              </select>
            </FormField>
            <FormField label="Filters (JSON)" full hint="Optional. Leave blank for all records in your school.">
              <textarea rows={2} value={filters} onChange={(e) => setFilters(e.target.value)} />
            </FormField>
          </div>
          <div className="form-actions">
            <button type="submit" disabled={busy}>{busy ? "Generating…" : "Generate export"}</button>
          </div>
        </form>

        {result && (
          <div style={{ marginTop: "1rem" }}>
            <div className="notice success">
              {result.record_count ?? 0} records staged.
              {result.id && (
                <> <a href={`${API_BASE}/kemis/exports/${result.id}/download/`}>Download {format}</a></>
              )}
            </div>
            {Array.isArray(result.preview) && result.preview.length > 0 && (
              <div style={{ overflowX: "auto" }}>
                <table className="data">
                  <thead><tr>{Object.keys(result.preview[0]).map((key) => <th key={key}>{key}</th>)}</tr></thead>
                  <tbody>
                    {result.preview.map((row, index) => (
                      <tr key={index}>{Object.keys(result.preview[0]).map((key) => <td key={key}>{String(row[key] ?? "")}</td>)}</tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>

      <div style={{ marginTop: "1.4rem" }}>
        <h2>Recent exports</h2>
        <DataTable
          columns={[
            { key: "reference", label: "Reference", render: (r) => <span className="mono">{r.reference}</span> },
            { key: "dataset", label: "Dataset", render: (r) => String(r.dataset || "").replace(/_/g, " ") },
            { key: "format", label: "Format" },
            { key: "record_count", label: "Records" },
            { key: "status", label: "Status", render: (r) => statusTag(r.status) },
            {
              key: "_download", label: "File", render: (row) => (
                <a href={`${API_BASE}/kemis/exports/${row.id}/download/`}>Download</a>
              ),
            },
          ]}
          rows={data}
          loading={loading}
          error={error}
          emptyTitle="No exports generated yet"
          emptyHint="Generate an export above to stage a local copy of school records."
        />
      </div>
    </section>
  );
}
