import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { useResource } from "../hooks/useApi";
import { api } from "../services/api";
import FormField from "../components/FormField";
import Loading from "../components/Loading";

const EDITABLE = [
  { name: "name", label: "Institution name", full: true, required: true },
  { name: "phone", label: "Phone number" },
  { name: "email", label: "Email address", type: "email" },
  { name: "website", label: "Website URL", type: "url" },
  { name: "motto", label: "School motto", full: true },
  { name: "address_line", label: "Physical address", full: true },
];

// School administrators register and maintain the school's own details here.
// The logo upload bypasses the JSON offline queue because files cannot be
// replayed from stored JSON.
export default function SchoolProfile() {
  const { user, setUser } = useAuth();
  const { push } = useToast();
  const { data, loading, error, reload } = useResource("/institutions/mine/");
  const [form, setForm] = useState({});
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    if (!data) return;
    setForm(Object.fromEntries(EDITABLE.map((field) => [
      field.name, data[field.name] ?? "",
    ])));
  }, [data]);

  async function refreshAuth() {
    try { setUser(await api.get("/auth/me/")); } catch { /* keep cached profile */ }
  }

  async function save(e) {
    e.preventDefault();
    setSaving(true);
    try {
      await api.patch("/institutions/mine/", form);
      push("School profile saved.", "success");
      reload();
      await refreshAuth();
    } catch (err) {
      push(err.message, "error");
    } finally {
      setSaving(false);
    }
  }

  async function uploadLogo(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const body = new FormData();
      body.append("logo", file);
      await api.upload("/institutions/mine/", body);
      push("School logo updated.", "success");
      reload();
      await refreshAuth();
    } catch (err) {
      push(err.message, "error");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  if (loading) return <Loading />;
  if (error) return <div className="notice error">{error}</div>;

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">School administration</div>
          <h1>School profile</h1>
          <p className="muted" style={{ marginTop: "0.2rem" }}>
            These details appear on staff and learner/guardian pages.
          </p>
        </div>
      </div>

      <div className="panel panel-pad" style={{ marginBottom: "1rem" }}>
        <div className="school-profile-header">
          <img
            src={data?.logo || "/mark.svg"}
            alt={`${data?.name || "School"} logo`}
            className="school-logo large"
            onError={(event) => { event.currentTarget.src = "/mark.svg"; }}
          />
          <div>
            <h2 style={{ marginBottom: "0.15rem" }}>{data?.name || "Your school"}</h2>
            <p className="muted" style={{ margin: 0 }}>
              Code <span className="mono">{data?.code || "—"}</span> · {data?.institution_type_name || "Institution"}
              {data?.county ? ` · ${data.county}` : ""}
            </p>
          </div>
        </div>
        <div className="school-logo-upload">
          <label htmlFor="school-logo">Change logo</label>
          <p className="muted" style={{ fontSize: "0.78rem", margin: "0 0 0.35rem" }}>
            JPG, PNG or WebP, maximum 2 MB. Requires an internet connection.
          </p>
          <input id="school-logo" type="file" accept="image/jpeg,image/png,image/webp" onChange={uploadLogo} disabled={uploading} />
          {uploading && <p className="muted">Uploading…</p>}
        </div>
      </div>

      <form className="panel panel-pad" onSubmit={save}>
        <div className="form-grid">
          {EDITABLE.map((field) => (
            <FormField key={field.name} label={field.label} full={field.full}>
              <input
                type={field.type || "text"}
                value={form[field.name] ?? ""}
                required={field.required}
                onChange={(e) => setForm({ ...form, [field.name]: e.target.value })}
              />
            </FormField>
          ))}
        </div>
        <div className="form-actions">
          <button type="submit" disabled={saving}>{saving ? "Saving…" : "Save school details"}</button>
        </div>
      </form>
    </section>
  );
}
