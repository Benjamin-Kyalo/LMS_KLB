import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { api } from "../services/api";
import { useToast } from "../context/ToastContext";
import FormField from "../components/FormField";
import { ROLES } from "../utilities/roles";

export default function Profile() {
  const { user, setUser } = useAuth();
  const { push } = useToast();
  const [form, setForm] = useState({
    first_name: user?.first_name || "", last_name: user?.last_name || "",
    email: user?.email || "", phone: user?.phone || "",
  });
  const [pw, setPw] = useState({ old_password: "", new_password: "" });
  const [busy, setBusy] = useState(false);

  async function saveProfile(e) {
    e.preventDefault();
    setBusy(true);
    try {
      const updated = await api.patch("/auth/me/", form);
      setUser(updated);
      push("Profile updated.", "success");
    } catch (err) { push(err.message, "error"); }
    finally { setBusy(false); }
  }

  async function changePassword(e) {
    e.preventDefault();
    setBusy(true);
    try {
      await api.post("/auth/password/change/", pw);
      push("Password changed.", "success");
      setPw({ old_password: "", new_password: "" });
    } catch (err) { push(err.message, "error"); }
    finally { setBusy(false); }
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
        <p className="muted">Role: <strong>{ROLES[user?.role] || user?.role}</strong> · Institution: {user?.institution_name || "Platform"}</p>
        <form onSubmit={saveProfile}>
          <div className="form-grid">
            <FormField label="First name"><input value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} /></FormField>
            <FormField label="Last name"><input value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} /></FormField>
            <FormField label="Email"><input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></FormField>
            <FormField label="Phone"><input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></FormField>
          </div>
          <div className="form-actions"><button disabled={busy}>Save profile</button></div>
        </form>
      </div>

      <div className="panel panel-pad">
        <h2>Change password</h2>
        <form onSubmit={changePassword}>
          <div className="form-grid">
            <FormField label="Current password"><input type="password" value={pw.old_password} onChange={(e) => setPw({ ...pw, old_password: e.target.value })} required /></FormField>
            <FormField label="New password"><input type="password" value={pw.new_password} onChange={(e) => setPw({ ...pw, new_password: e.target.value })} required /></FormField>
          </div>
          <div className="form-actions"><button disabled={busy}>Change password</button></div>
        </form>
      </div>
    </section>
  );
}
