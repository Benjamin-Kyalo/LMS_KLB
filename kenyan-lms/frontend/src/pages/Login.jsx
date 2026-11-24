import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { canUseAdmin, homeFor, ROLES } from "../utilities/roles";

export default function Login({ variant = "standard" }) {
  const { signIn, loading, error } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [localError, setLocalError] = useState(null);
  const role = String(params.get("role") || "").toUpperCase();
  const isAdmin = variant === "admin";

  async function handleSubmit(e) {
    e.preventDefault();
    setLocalError(null);
    try {
      const data = await signIn(username, password);
      if (isAdmin && !canUseAdmin(data.user)) {
        setLocalError("This account uses the learner and guardian portal, not the staff portal.");
        return;
      }
      if (data.must_change_password) {
        navigate(isAdmin || canUseAdmin(data.user) ? "/admin/profile" : "/portal/profile");
        return;
      }
      navigate(variant === "portal" ? "/portal" : homeFor(data.user));
    } catch { /* error shown from context */ }
  }

  return (
    <div className="login-page">
      <div className="login-story">
        <div className="display" style={{ fontSize: "1.6rem", fontWeight: 700 }}>KLB Learning Ecosystem</div>
        <div>
          <h1 style={{ color: "var(--paper)", fontSize: "2.4rem", lineHeight: 1.15 }}>
            {isAdmin ? "One administration portal for the whole school." : "One platform for teaching, records and textbooks."}
          </h1>
          <p style={{ color: "#cfe0d6", maxWidth: 420 }}>
            Built for Kenyan schools: competency-based learning, school administration
            and a digital publishing library — designed to work on modest connections.
          </p>
        </div>
        <div className="muted" style={{ color: "#9fb8ab", fontSize: "0.8rem" }}>Kenya Literature Bureau · Digital Education</div>
      </div>

      <div className="login-panel">
        <form onSubmit={handleSubmit} style={{ width: "100%", maxWidth: 380 }}>
          <div className="overline">{isAdmin ? "Administration portal" : "Sign in"}</div>
          <h1>{isAdmin ? "Administrator sign in" : "Welcome back"}</h1>
          <p className="muted">
            {isAdmin
              ? "Use an administrator account issued by your institution or platform administrator."
              : "Use the account your school administrator created, or register below."}
          </p>
          {role && ROLES[role] && (
            <div className="notice info" style={{ margin: "0.75rem 0" }}>Signing in as {ROLES[role]}</div>
          )}
          {params.get("registered") === "teacher" && (
            <div className="notice warn" style={{ margin: "0.75rem 0" }}>
              Your teacher account was created. It becomes active after approval by a school administrator.
            </div>
          )}
          {(error || localError) && <div className="notice error" style={{ margin: "0.75rem 0" }}>{localError || error}</div>}
          <div style={{ margin: "0.9rem 0" }}>
            <label htmlFor="username">Username</label>
            <input id="username" value={username} onChange={(e) => setUsername(e.target.value)} required autoFocus />
          </div>
          <div style={{ margin: "0.9rem 0" }}>
            <label htmlFor="password">Password</label>
            <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          <button type="submit" disabled={loading} style={{ width: "100%" }}>
            {loading ? "Signing in…" : "Sign in"}
          </button>
          <div className="login-links">
            {isAdmin ? (
              <>
                <Link to="/admin/signup">Redeem an administrator invitation</Link>
                <Link to="/">Back to homepage</Link>
              </>
            ) : (
              <>
                <Link to="/register">Create a learner, guardian or teacher account</Link>
              </>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}
