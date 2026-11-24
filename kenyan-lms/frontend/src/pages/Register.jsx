import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api, listAll } from "../services/api";
import { useAuth } from "../context/AuthContext";
import { homeFor } from "../utilities/roles";

const ROLE_OPTIONS = [
  { value: "LEARNER", label: "Learner", note: "Courses, assignments and results" },
  { value: "GUARDIAN", label: "Parent / Guardian", note: "Follow a learner's progress" },
  { value: "TEACHER", label: "Teacher", note: "Created pending school approval" },
];

export default function Register() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { signIn } = useAuth();
  const [schools, setSchools] = useState([]);
  const [loadingSchools, setLoadingSchools] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState(null);
  const requestedRole = String(params.get("role") || "").toUpperCase();
  const [form, setForm] = useState({
    username: "", email: "", password: "", confirm: "", first_name: "",
    last_name: "", role: ROLE_OPTIONS.some((r) => r.value === requestedRole) ? requestedRole : "LEARNER",
    institution: "", phone: "", date_of_birth: "", gender: "",
    relationship_to_learner: "", occupation: "", employment_type: "CONTRACT",
  });

  useEffect(() => {
    let active = true;
    listAll("/institutions/public-institutions/")
      .then((rows) => { if (active) setSchools(rows); })
      .catch((err) => { if (active) setError(err.message); })
      .finally(() => { if (active) setLoadingSchools(false); });
    return () => { active = false; };
  }, []);

  function update(name, value) {
    setForm((previous) => ({ ...previous, [name]: value }));
  }

  async function submit(e) {
    e.preventDefault();
    setError(null);
    setNotice(null);
    if (form.password !== form.confirm) {
      setError("Passwords do not match.");
      return;
    }
    const payload = { ...form };
    delete payload.confirm;
    Object.keys(payload).forEach((key) => {
      if (payload[key] === "") delete payload[key];
    });
    setSaving(true);
    try {
      await api.post("/auth/register/", payload);
      if (form.role === "TEACHER") {
        setNotice("Teacher account created. A school administrator must approve it before you can sign in.");
        setTimeout(() => navigate("/login?registered=teacher"), 1800);
        return;
      }
      const data = await signIn(form.username, form.password);
      navigate(homeFor(data.user));
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
        <nav aria-label="Registration navigation">
          <Link to="/login">Sign in</Link>
        </nav>
      </header>

      <main className="public-auth-main">
        <div className="public-auth-copy">
          <div className="overline">Create your account</div>
          <h1>Choose your role, then fill in only what applies.</h1>
          <p>
            Learner and guardian accounts are ready to use immediately. Teacher accounts are
            created pending approval by the school. Administrator accounts require a secure,
            single-use invitation token and are never created through this form.
          </p>
          <div className="notice info" style={{ marginTop: "1rem" }}>
            The school database is shared: accounts created here appear in the administration
            portal for the same institution.
          </div>
        </div>

        <form className="public-auth-card" onSubmit={submit}>
          <h2>Register</h2>
          {error && <div className="notice error">{error}</div>}
          {notice && <div className="notice success">{notice}</div>}

          <fieldset className="role-picker">
            <legend>Account type</legend>
            <div className="role-options">
              {ROLE_OPTIONS.map((item) => (
                <label key={item.value} className={form.role === item.value ? "selected" : ""}>
                  <input
                    type="radio" name="role" value={item.value}
                    checked={form.role === item.value}
                    onChange={() => update("role", item.value)}
                  />
                  <span><strong>{item.label}</strong><small>{item.note}</small></span>
                </label>
              ))}
            </div>
          </fieldset>

          <div className="form-grid">
            <FormInput label="First name" value={form.first_name} onChange={(v) => update("first_name", v)} required />
            <FormInput label="Last name" value={form.last_name} onChange={(v) => update("last_name", v)} required />
            <FormInput label="Username" value={form.username} onChange={(v) => update("username", v)} required />
            <FormInput label="Email" type="email" value={form.email} onChange={(v) => update("email", v)} required />
            <FormInput label="Password" type="password" value={form.password} onChange={(v) => update("password", v)} required hint="At least 8 characters" />
            <FormInput label="Confirm password" type="password" value={form.confirm} onChange={(v) => update("confirm", v)} required />

            <label>
              School / institution
              <select value={form.institution} onChange={(e) => update("institution", e.target.value)} required>
                <option value="">— choose —</option>
                {schools.map((school) => (
                  <option key={school.id} value={school.id}>{school.name} ({school.code})</option>
                ))}
              </select>
            </label>
            <FormInput label="Phone" value={form.phone} onChange={(v) => update("phone", v)} />

            {form.role === "LEARNER" && (
              <>
                <FormInput label="Date of birth" type="date" value={form.date_of_birth} onChange={(v) => update("date_of_birth", v)} required />
                <label>
                  Gender
                  <select value={form.gender} onChange={(e) => update("gender", e.target.value)} required>
                    <option value="">— choose —</option>
                    <option value="F">Female</option>
                    <option value="M">Male</option>
                    <option value="OTHER">Other</option>
                  </select>
                </label>
              </>
            )}
            {form.role === "GUARDIAN" && (
              <>
                <FormInput label="Relationship to learner" value={form.relationship_to_learner} onChange={(v) => update("relationship_to_learner", v)} required />
                <FormInput label="Occupation" value={form.occupation} onChange={(v) => update("occupation", v)} />
              </>
            )}
            {form.role === "TEACHER" && (
              <label>
                Employment type
                <select value={form.employment_type} onChange={(e) => update("employment_type", e.target.value)} required>
                  <option value="PERMANENT">Permanent</option>
                  <option value="CONTRACT">Contract</option>
                  <option value="PART_TIME">Part time</option>
                  <option value="VOLUNTEER">Volunteer</option>
                </select>
              </label>
            )}
          </div>

          <div className="form-actions">
            <button type="submit" disabled={saving || loadingSchools}>
              {saving ? "Creating…" : "Create account"}
            </button>
          </div>
          <p className="muted" style={{ fontSize: "0.82rem" }}>
            Already registered? <Link to="/login">Sign in</Link>
          </p>
        </form>
      </main>
    </div>
  );
}

function FormInput({ label, value, onChange, type = "text", required, hint }) {
  return (
    <label>
      {label}
      <input type={type} value={value} onChange={(e) => onChange(e.target.value)} required={required} />
      {hint && <small className="muted">{hint}</small>}
    </label>
  );
}
