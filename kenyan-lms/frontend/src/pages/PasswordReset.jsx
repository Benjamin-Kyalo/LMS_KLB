import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../services/api";
import { useToast } from "../context/ToastContext";
import PublicHeader from "../components/PublicHeader";
import PublicFooter from "../components/PublicFooter";
import AnimatedSubmitButton from "../components/AnimatedSubmitButton";

export default function PasswordReset() {
  const { uid, token } = useParams();
  const navigate = useNavigate();
  const { push } = useToast();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState(null);

  const confirming = Boolean(uid && token);

  useEffect(() => {
    if (!confirming) return;
    setMessage("Choose a new password for your account.");
  }, [confirming]);

  async function requestReset(e) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      await api.post("/auth/password/reset/request/", { email });
      setMessage("If the account exists, a reset message has been sent.");
      push("Reset request submitted.", "success");
    } catch (err) {
      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  async function confirmReset(e) {
    e.preventDefault();
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await api.post("/auth/password/reset/confirm/", {
        uid,
        token,
        new_password: password,
      });
      push("Password reset. You may now sign in.", "success");
      navigate("/login");
    } catch (err) {
      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="public-auth-page">
      <PublicHeader links={[]} ariaLabel="Password reset navigation" showSignIn={false} />
      <main className="public-auth-main">
        <div className="public-auth-card">
          <h2>{confirming ? "Set a new password" : "Reset your password"}</h2>
          {message && <div className="notice info" role="status">{message}</div>}
          {error && <div className="notice error" role="alert">{error}</div>}
          {confirming ? (
            <form onSubmit={confirmReset}>
              <div style={{ margin: "0.9rem 0" }}>
                <label htmlFor="new-password">New password</label>
                <input id="new-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
              </div>
              <div style={{ margin: "0.9rem 0" }}>
                <label htmlFor="confirm-password">Confirm password</label>
                <input id="confirm-password" type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required />
              </div>
              <AnimatedSubmitButton disabled={saving} style={{ width: "100%" }}>
                {saving ? "Resetting…" : "Reset password"}
              </AnimatedSubmitButton>
            </form>
          ) : (
            <form onSubmit={requestReset}>
              <div style={{ margin: "0.9rem 0" }}>
                <label htmlFor="email">Email address</label>
                <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
              </div>
              <AnimatedSubmitButton disabled={saving} style={{ width: "100%" }}>
                {saving ? "Sending…" : "Send reset link"}
              </AnimatedSubmitButton>
            </form>
          )}
        </div>
      </main>
      <PublicFooter />
    </div>
  );
}
PY