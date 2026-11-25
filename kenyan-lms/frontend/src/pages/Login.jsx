import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useSiteContent } from "../context/SiteContentContext";
import PublicFooter from "../components/PublicFooter";
import ParticleHeadline from "../components/ParticleHeadline";
import AnimatedSubmitButton from "../components/AnimatedSubmitButton";
import RollingLabel from "../components/RollingLabel";
import { useSectionStyle } from "../styles/sectionStyles";
import { canUseAdmin, homeFor, ROLES } from "../utilities/roles";

export default function Login({ variant = "standard" }) {
  const { signIn, loading, error } = useAuth();
  const { content } = useSiteContent();
  const loginCopy = content.auth.login;
  const hero = content.hero;
  const navigate = useNavigate();
  const sectionStyle = useSectionStyle("login");
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
      if (data.user?.onboarding?.is_complete === false) {
        navigate("/onboarding");
        return;
      }
      navigate(variant === "portal" ? "/portal" : homeFor(data.user));
    } catch { /* error shown from context */ }
  }

  return (
    <>
      <main className="login-page">
        <div className="login-story section-styled" style={sectionStyle}>
          <img
            className="login-story-photo"
            src={loginCopy.storyImageSrc || hero.imageSrc || "/images/signin-time.jpg"}
            alt=""
            aria-hidden="true"
          />
          <div className="login-story-scrim" aria-hidden="true" />
          <div className="display" style={{ fontSize: "1.6rem", fontWeight: 700 }}>
            {content.header.brand.name}
          </div>
          <div>
            <ParticleHeadline
              text={isAdmin ? loginCopy.adminHeading : loginCopy.publicHeading}
              className="auth-story-headline"
            />
            <p className="auth-story-copy auth-copy-reveal auth-copy-reveal--delayed">
              {loginCopy.storyCopy}
            </p>
          </div>
          <div className="muted" style={{ color: "var(--ramp-300)", fontSize: "0.8rem" }}>
            {loginCopy.footnote}
          </div>
        </div>

        <div className="login-panel">
          <form className="auth-card-enter" onSubmit={handleSubmit} style={{ width: "100%", maxWidth: 380 }}>
            <div className="overline">{isAdmin ? "Administration portal" : "Sign in"}</div>
            <h2>{isAdmin ? "Administrator sign in" : "Welcome back"}</h2>
            <p className="muted">
              {isAdmin ? loginCopy.adminIntro : loginCopy.publicIntro}
            </p>
            {role && ROLES[role] && (
              <div className="notice info" style={{ margin: "0.75rem 0" }}>Signing in as {ROLES[role]}</div>
            )}
            {params.get("registered") === "teacher" && (
              <div className="notice warn" style={{ margin: "0.75rem 0" }}>
                Your teacher account was created. It becomes active after approval by a school administrator.
              </div>
            )}
            {(error || localError) && (
              <div className="notice error" role="alert" style={{ margin: "0.75rem 0" }}>
                {localError || error}
              </div>
            )}
            <div style={{ margin: "0.9rem 0" }}>
              <label htmlFor="username">Username</label>
              <input id="username" value={username} onChange={(e) => setUsername(e.target.value)} required autoFocus />
            </div>
            <div style={{ margin: "0.9rem 0" }}>
              <label htmlFor="password">Password</label>
              <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            </div>
            <AnimatedSubmitButton disabled={loading} style={{ width: "100%" }}>
              {loading ? "Signing in…" : "Sign in"}
            </AnimatedSubmitButton>
            <div className="login-links">
              {isAdmin ? (
                <>
                  <Link to="/admin/signup" className="button-link login-link-primary">
                    <RollingLabel>Redeem an administrator invitation</RollingLabel>
                  </Link>
                  <Link to="/" className="button-link login-link-secondary">
                    <RollingLabel>Back to homepage</RollingLabel>
                  </Link>
                </>
              ) : (
                <>
                  <Link to="/reset-password" className="button-link login-link-secondary">
                    <RollingLabel>Forgot your password?</RollingLabel>
                  </Link>
                  <Link to="/register" className="button-link login-link-primary">
                    <RollingLabel>Create a learner, guardian or teacher account</RollingLabel>
                  </Link>
                </>
              )}
            </div>
          </form>
        </div>
      </main>
      <PublicFooter />
    </>
  );
}
