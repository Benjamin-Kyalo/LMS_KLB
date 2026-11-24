import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../services/api";
import { useAuth } from "../context/AuthContext";

export default function AdminSignup() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { signInWithData } = useAuth();
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
      <header className="public-topbar">
        <Link to="/" className="public-brand">
          <span className="public-mark">KLB</span>
          <span><strong>Digital Learning Ecosystem</strong><small>Kenya Literature Bureau</small></span>
        </Link>
        <nav aria-label="Admin authentication navigation">
          <Link to="/admin/login">Admin sign in</Link>
          <Link to="/register">User registration</Link>
        </nav>
      </header>

      <main className="public-auth-main">
        <div className="public-auth-copy">
          <div className="overline">Administration portal</div>
          <h1>Administrator accounts are invitation-only.</h1>
          <p>
            A platform or school administrator must issue a secure, single-use invitation token.
            The invitation fixes the role and institution; this form cannot grant administrator
            privileges by itself. Each invitation works once and expires after seven days.
          </p>
          <div className="notice warn" style={{ marginTop: "1rem" }}>
            Do not share invitation tokens or passwords over unsecured channels. If you do not
            have a token, contact your platform administrator.
          </div>
        </div>

        <form className="public-auth-card" onSubmit={submit}>
          <h2>Redeem an invitation</h2>
          {error && <div className="notice error">{error}</div>}
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
            <button type="submit" disabled={saving}>{saving ? "Creating account…" : "Create administrator account"}</button>
          </div>
          <p className="muted" style={{ fontSize: "0.82rem" }}>
            Already have an account? <Link to="/admin/login">Sign in to the admin portal</Link>
          </p>
        </form>
      </main>
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
