import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../services/api";
import { useAuth } from "../context/AuthContext";
import { useSiteContent } from "../context/SiteContentContext";
import PublicHeader from "../components/PublicHeader";
import PublicFooter from "../components/PublicFooter";
import AnimatedSubmitButton from "../components/AnimatedSubmitButton";
import { useSectionStyle } from "../styles/sectionStyles";

export default function AdminSignup() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { signInWithData } = useAuth();
  const { content } = useSiteContent();
  const sectionStyle = useSectionStyle("invite");
  const adminCopy = content.auth.admin;
  const [form, setForm] = useState({
    token: params.get("token") || "", username: "", email: "",
    first_name: "", last_name: "", password: "", confirm: "",
  });
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  function update(name, value) {
    setForm((previous) => ({ ...previous, [name]: value }));
  }

  async function submit(e) {
    e.preventDefault();
    setError(null);
    if (form.password !== form.confirm) {
      setError("Passwords do not match.");
      return;
    }
    setSaving(true);
    try {
      const payload = { ...form };
      delete payload.confirm;
      const data = await api.post("/auth/admin-invitations/accept/", payload);
      signInWithData(data);
      navigate("/admin");
    } catch (err) {
      setError(err.details ? JSON.stringify(err.details) : err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="public-auth-page">
      <PublicHeader
        links={content.header.adminLinks}
        ariaLabel="Admin authentication navigation"
        showSignIn={false}
      />

      <main className="public-auth-main view-enter section-styled" style={sectionStyle}>
        <div className="public-auth-copy">
          <div className="overline">{adminCopy.overline}</div>
          <h1>{adminCopy.heading}</h1>
          <p>{adminCopy.copy}</p>
          <div className="notice warn" role="status" style={{ marginTop: "1rem" }}>
            {adminCopy.warning}
          </div>
        </div>

        <form className="public-auth-card auth-card-enter" onSubmit={submit}>
          <h2>Redeem an invitation</h2>
          {error && <div className="notice error" role="alert">{error}</div>}
          <div className="form-grid">
            <label className="full">
              Invitation token
              <input value={form.token} onChange={(e) => update("token", e.target.value)} required />
              <small className="muted">Paste the complete token supplied by your administrator.</small>
            </label>
            <label className="full invite-preview">
              The role and school are taken from the token; they are not chosen here.
            </label>
            <FormInput label="Username" value={form.username} onChange={(v) => update("username", v)} required />
            <FormInput label="Email (must match invitation)" type="email" value={form.email} onChange={(v) => update("email", v)} required />
            <FormInput label="First name" value={form.first_name} onChange={(v) => update("first_name", v)} required />
            <FormInput label="Last name" value={form.last_name} onChange={(v) => update("last_name", v)} required />
            <FormInput label="Password" type="password" value={form.password} onChange={(v) => update("password", v)} required />
            <FormInput label="Confirm password" type="password" value={form.confirm} onChange={(v) => update("confirm", v)} required />
          </div>
          <div className="form-actions">
            <AnimatedSubmitButton disabled={saving}>
              {saving ? "Creating account…" : "Create administrator account"}
            </AnimatedSubmitButton>
          </div>
          <p className="muted" style={{ fontSize: "0.82rem" }}>
            Already have an account? <Link to="/admin/login">Sign in to the admin portal</Link>
          </p>
        </form>
      </main>
      <PublicFooter />
    </div>
  );
}

function FormInput({ label, value, onChange, type = "text", required }) {
  return (
    <label>
      {label}
      <input type={type} value={value} onChange={(e) => onChange(e.target.value)} required={required} />
    </label>
  );
}
