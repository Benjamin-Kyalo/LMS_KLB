import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { api } from "../services/api";
import { useToast } from "../context/ToastContext";
import FormField from "../components/FormField";
import RollingLabel from "../components/RollingLabel";
import { roleLabel } from "../utilities/roles";

export default function Profile() {
  const { user, setUser } = useAuth();
  const { push } = useToast();
  const [form, setForm] = useState({
    first_name: user?.first_name || "", last_name: user?.last_name || "",
    email: user?.email || "", phone: user?.phone || "",
  });
  const [pw, setPw] = useState({ old_password: "", new_password: "" });
  const [profileBusy, setProfileBusy] = useState(false);
  const [passwordBusy, setPasswordBusy] = useState(false);
  const [profileSaved, setProfileSaved] = useState(false);
  const [passwordSaved, setPasswordSaved] = useState(false);

  async function saveProfile(e) {
    e.preventDefault();
    setProfileBusy(true);
    setProfileSaved(false);
    try {
      const updated = await api.patch("/auth/me/", form);
      setUser(updated);
      push("Profile updated.", "success");
      setProfileSaved(true);
      setTimeout(() => setProfileSaved(false), 1400);
    } catch (err) { push(err.message, "error"); }
    finally { setProfileBusy(false); }
  }

  async function changePassword(e) {
    e.preventDefault();
    setPasswordBusy(true);
    setPasswordSaved(false);
    try {
      await api.post("/auth/password/change/", pw);
      push("Password changed.", "success");
      setPw({ old_password: "", new_password: "" });
      setPasswordSaved(true);
      setTimeout(() => setPasswordSaved(false), 1400);
    } catch (err) { push(err.message, "error"); }
    finally { setPasswordBusy(false); }
  }

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">Account</div>
          <h1>Profile</h1>
        </div>
      </div>

      <div className="panel panel-pad" style={{ marginBottom: "1rem" }}>
        <p className="muted">Role: <strong>{roleLabel(user)}</strong> · Institution: {user?.institution_name || "Platform"}</p>
        <form onSubmit={saveProfile}>
          <div className="form-grid">
            <FormField label="First name"><input value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} /></FormField>
            <FormField label="Last name"><input value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} /></FormField>
            <FormField label="Email"><input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></FormField>
            <FormField label="Phone"><input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></FormField>
          </div>
          <div className="form-actions">
            <button disabled={profileBusy} aria-busy={profileBusy || undefined}>
              {profileSaved ? "Profile saved ✓" : profileBusy ? "Saving…" : <RollingLabel>Save profile</RollingLabel>}
            </button>
          </div>
          {profileSaved && <p role="status" className="muted" style={{ margin: "0.35rem 0 0" }}>Profile saved.</p>}
        </form>
      </div>

      <div className="panel panel-pad">
        <h2>Change password</h2>
        <form onSubmit={changePassword}>
          <div className="form-grid">
            <FormField label="Current password"><input type="password" value={pw.old_password} onChange={(e) => setPw({ ...pw, old_password: e.target.value })} required /></FormField>
            <FormField label="New password"><input type="password" value={pw.new_password} onChange={(e) => setPw({ ...pw, new_password: e.target.value })} required /></FormField>
          </div>
          <div className="form-actions">
            <button disabled={passwordBusy} aria-busy={passwordBusy || undefined}>
              {passwordSaved ? "Password updated ✓" : passwordBusy ? "Updating…" : <RollingLabel>Change password</RollingLabel>}
            </button>
          </div>
          {passwordSaved && <p role="status" className="muted" style={{ margin: "0.35rem 0 0" }}>Password updated.</p>}
        </form>
      </div>
    </section>
  );
}
