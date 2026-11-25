import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api, listAll } from "../services/api";
import { useAuth } from "../context/AuthContext";
import { useSiteContent } from "../context/SiteContentContext";
import PublicHeader from "../components/PublicHeader";
import PublicFooter from "../components/PublicFooter";
import ParticleHeadline from "../components/ParticleHeadline";
import AnimatedSubmitButton from "../components/AnimatedSubmitButton";
import { useSectionStyle } from "../styles/sectionStyles";
import { homeFor } from "../utilities/roles";

export default function Register() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { signIn } = useAuth();
  const { content } = useSiteContent();
  const sectionStyle = useSectionStyle("register");
  const registerCopy = content.auth.register;
  const roleOptions = registerCopy.roleOptions || [];
  const [schools, setSchools] = useState([]);
  const [loadingSchools, setLoadingSchools] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState(null);
  const requestedRole = String(params.get("role") || "").toUpperCase();
  const [form, setForm] = useState({
    username: "", email: "", password: "", confirm: "", first_name: "",
    last_name: "", role: roleOptions.some((r) => r.value === requestedRole) ? requestedRole : roleOptions[0]?.value || "LEARNER",
    institution: "", phone: "", date_of_birth: "", gender: "",
    relationship_to_learner: "", learner_identifier: "", occupation: "", employment_type: "CONTRACT",
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
      navigate(data.user?.onboarding?.is_complete === false ? "/onboarding" : homeFor(data.user));
    } catch (err) {
      setError(err.details ? JSON.stringify(err.details) : err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="public-auth-page">
      <PublicHeader links={content.header.authLinks} ariaLabel="Registration navigation" showSignIn={false} />

      <main className="public-auth-main view-enter section-styled" style={sectionStyle}>
        <img
          className="public-auth-photo"
          src={registerCopy.storyImageSrc || "/images/register-learn.jpg"}
          alt=""
          aria-hidden="true"
        />
        <div className="public-auth-photo-scrim" aria-hidden="true" />
        <div className="public-auth-copy">
          <div className="overline">{registerCopy.overline}</div>
          <ParticleHeadline text={registerCopy.heading} className="public-auth-headline" />
          <p className="auth-copy-reveal auth-copy-reveal--delayed">{registerCopy.copy}</p>
          <div
            className="notice info auth-copy-reveal auth-copy-reveal--delayed"
            style={{ marginTop: "1rem" }}
          >
            {registerCopy.notice}
          </div>
        </div>

        <form className="public-auth-card auth-card-enter" onSubmit={submit}>
          <h2>Register</h2>
          <ol className="form-steps" aria-label="Registration steps">
            {(registerCopy.steps || []).map((step, index) => (
              <li key={step}><span>{index + 1}</span> {step}</li>
            ))}
          </ol>
          {error && <div className="notice error" role="alert">{error}</div>}
          {notice && <div className="notice success" role="status">{notice}</div>}

          <fieldset className="role-picker">
            <legend>Account type</legend>
            <div className="role-options">
              {roleOptions.map((item) => (
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
            <FormInput label="Username" value={form.username} onChange={(v) => update("username", v)} hint="Leave blank to generate from your name." />
            <FormInput label="Email" type="email" value={form.email} onChange={(v) => update("email", v)} required />
            <FormInput label="Password" type="password" value={form.password} onChange={(v) => update("password", v)} required hint="At least 8 characters" />
            <FormInput label="Confirm password" type="password" value={form.confirm} onChange={(v) => update("confirm", v)} required />

            <label>
              School / institution
              <select value={form.institution} onChange={(e) => update("institution", e.target.value)} required>
                <option value="">Choose one</option>
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
                    <option value="">Choose one</option>
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
                <FormInput
                  label="Learner admission or assessment number"
                  value={form.learner_identifier}
                  onChange={(v) => update("learner_identifier", v)}
                  required
                  hint="Your school verifies this link before any learner data is shown."
                />
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
            <AnimatedSubmitButton disabled={saving || loadingSchools}>
              {saving ? "Creating…" : "Create account"}
            </AnimatedSubmitButton>
          </div>
          <p className="muted" style={{ fontSize: "0.82rem" }}>
            Already registered? <Link to="/login">Sign in</Link>
          </p>
        </form>
      </main>
      <PublicFooter />
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
