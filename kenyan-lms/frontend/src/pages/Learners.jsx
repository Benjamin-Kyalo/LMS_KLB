import { useState } from "react";
import { useList } from "../hooks/useApi";
import { api } from "../services/api";
import { useToast } from "../context/ToastContext";
import { useAuth } from "../context/AuthContext";
import { isAdmin, isTeacher } from "../utilities/roles";
import DataTable from "../components/DataTable";
import Modal from "../components/Modal";
import FormField from "../components/FormField";
import LinkConfirmation from "../components/LinkConfirmation";
import LinkPermissions from "../components/LinkPermissions";
import PersonSearchSelect from "../components/PersonSearchSelect";
import RollingLabel from "../components/RollingLabel";
import { TablePagination, TableToolbar } from "../components/TableTools";
import usePendingLinkRequest from "../hooks/usePendingLinkRequest";
import useTableControls from "../hooks/useTableControls";
import { statusTag } from "../utilities/format";

export default function Learners() {
  const { user } = useAuth();
  const canWrite = isAdmin(user) || isTeacher(user);
  const { data, loading, error, reload } = useList("/learners/");
  const { data: classes } = useList("/institutions/classes/");
  const { push } = useToast();
  const controls = useTableControls(data);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({});
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [linkTarget, setLinkTarget] = useState(null);
  const [linkForm, setLinkForm] = useState({
    guardian: null,
    relationship: "Parent",
    is_primary: true,
    can_view_academics: true,
    can_view_attendance: true,
    can_view_fees: false,
  });
  const [linkSaving, setLinkSaving] = useState(false);
  const [linkError, setLinkError] = useState(null);
  const [linkConfirmed, setLinkConfirmed] = useState(false);

  const selectedGuardian = linkForm.guardian;
  const { request: pendingRequest, clear: clearPendingRequest } = usePendingLinkRequest(
    selectedGuardian?.id, linkTarget?.id
  );
  const existingGuardians = linkTarget?.guardian_names || [];
  const guardianAlreadyLinked = Boolean(selectedGuardian && (
    (linkTarget?.guardian_ids || []).some((id) => String(id) === String(selectedGuardian.id))
    || existingGuardians.some(
      (name) => String(name).toLowerCase() === String(selectedGuardian.guardian_name || "").toLowerCase()
    )
  ));
  const otherLearners = selectedGuardian?.learner_names || [];
  const linkNeedsConfirmation = !guardianAlreadyLinked && Boolean(
    existingGuardians.length || otherLearners.length || pendingRequest
  );
  const linkPermissionFields = {
    can_view_academics: linkForm.can_view_academics,
    can_view_attendance: linkForm.can_view_attendance,
    can_view_fees: linkForm.can_view_fees,
  };

  function requestDecided() {
    clearPendingRequest();
    setLinkConfirmed(false);
    setLinkTarget(null);
    reload();
  }

  function startCreate() {
    setEditing(null);
    setForm({ username: "", first_name: "", last_name: "", email: "", admission_number: "", assessment_number: "", class_room: "", date_of_birth: "", gender: "", status: "ACTIVE" });
    setFormError(null);
    setOpen(true);
  }

  function startEdit(row) {
    setEditing(row);
    setForm({
      username: row.username || "",
      first_name: row.first_name || "",
      last_name: row.last_name || "",
      email: row.email || "",
      admission_number: row.admission_number || "",
      assessment_number: row.assessment_number || "",
      class_room: row.class_room || "",
      date_of_birth: row.date_of_birth || "",
      gender: row.gender || "",
      status: row.status || "ACTIVE",
    });
    setFormError(null);
    setOpen(true);
  }

  async function save(e) {
    e.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      if (editing) {
        await api.patch(`/learners/${editing.id}/`, form);
        push("Learner updated.", "success");
      } else {
        await api.post("/learners/", form);
        push("Learner registered.", "success");
      }
      setOpen(false);
      setEditing(null);
      reload();
    } catch (err) {
      setFormError(err.message || "Something went wrong. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  async function remove(row) {
    try {
      await api.del(`/learners/${row.id}/`);
      push("Learner deleted.", "success");
      reload();
    } catch (err) { push(err.message, "error"); }
  }

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">Student information</div>
          <h1>Learners</h1>
        </div>
        <div className="actions">
          {canWrite && <button onClick={startCreate}><RollingLabel>Register learner</RollingLabel></button>}
        </div>
      </div>

      <TableToolbar title="learners" controls={controls} onRefresh={reload} />

      <DataTable
        columns={[
          { key: "learner_name", label: "Name", render: (r) => r.learner_name || r.full_name || "—" },
          { key: "username", label: "Username", render: (r) => r.username || "—" },
          { key: "admission_number", label: "Admission no.", render: (r) => <span className="mono">{r.admission_number}</span> },
          { key: "institution_code", label: "School code", render: (r) => r.institution_code || "—" },
          { key: "class_name", label: "Class", render: (r) => r.class_name || "—" },
          { key: "guardian_names", label: "Guardians", render: (r) => {
            const names = r.guardian_names || [];
            return names.length
              ? <><span className="tag good">Linked</span> {names.join(", ")}</>
              : <span className="tag warn">Not linked</span>;
          } },
          { key: "status", label: "Status", render: (r) => statusTag(r.status) },
          { key: "_actions", label: "Actions", render: (r) => canWrite && (
            <div className="row-actions">
              <button className="small" onClick={() => { setLinkTarget(r); setLinkForm({ guardian: null, relationship: "Parent", is_primary: true, can_view_academics: true, can_view_attendance: true, can_view_fees: false }); setLinkError(null); setLinkConfirmed(false); }}>
                <RollingLabel>{(r.guardian_names || []).length ? "Add guardian" : "Link guardian"}</RollingLabel>
              </button>
              <button className="ghost small" onClick={() => startEdit(r)}><RollingLabel>Edit</RollingLabel></button>
              <button className="ghost small danger" onClick={() => setDeleteTarget(r)}><RollingLabel>Delete</RollingLabel></button>
            </div>
          ) },
        ]}
        rows={controls.visibleRows} loading={loading} error={error}
        emptyTitle={controls.query ? "No matching learners" : "No learners yet"}
        emptyHint="Register your first learner to begin."
      />

      {!loading && !error && <TablePagination controls={controls} />}

      {open && (
        <Modal title={editing ? "Edit learner" : "Register learner"} onClose={() => { setOpen(false); setEditing(null); }}>
          <form onSubmit={save}>
            {formError && <div className="notice error" role="alert" style={{ marginBottom: "0.75rem" }}>{formError}</div>}
            <div className="form-grid">
              <FormField label="Username" hint="Leave blank to keep current."><input value={form.username || ""} onChange={(e) => setForm({ ...form, username: e.target.value })} /></FormField>
              <FormField label="First name"><input value={form.first_name || ""} onChange={(e) => setForm({ ...form, first_name: e.target.value })} required /></FormField>
              <FormField label="Last name"><input value={form.last_name || ""} onChange={(e) => setForm({ ...form, last_name: e.target.value })} required /></FormField>
              <FormField label="Email"><input type="email" value={form.email || ""} onChange={(e) => setForm({ ...form, email: e.target.value })} /></FormField>
              <FormField label="Admission number" hint="Leave blank to generate automatically."><input value={form.admission_number} onChange={(e) => setForm({ ...form, admission_number: e.target.value })} /></FormField>
              <FormField label="Assessment number"><input value={form.assessment_number} onChange={(e) => setForm({ ...form, assessment_number: e.target.value })} /></FormField>
              <FormField label="Class">
                <select value={form.class_room || ""} onChange={(e) => setForm({ ...form, class_room: e.target.value })}>
                  <option value="">— choose —</option>
                  {(classes || []).map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.display_name || [item.name, item.stream].filter(Boolean).join(" ")}
                    </option>
                  ))}
                </select>
              </FormField>
              <FormField label="Date of birth"><input type="date" value={form.date_of_birth || ""} onChange={(e) => setForm({ ...form, date_of_birth: e.target.value })} /></FormField>
              <FormField label="Gender">
                <select value={form.gender || ""} onChange={(e) => setForm({ ...form, gender: e.target.value })}>
                  <option value="">Choose one</option>
                  <option value="F">Female</option>
                  <option value="M">Male</option>
                  <option value="OTHER">Other</option>
                </select>
              </FormField>
              {editing && (
                <FormField label="Status">
                  <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
                    <option value="ACTIVE">Active</option>
                    <option value="TRANSFERRED">Transferred</option>
                    <option value="ALUMNI">Alumni</option>
                    <option value="SUSPENDED">Suspended</option>
                  </select>
                </FormField>
              )}
            </div>
            <div className="form-actions">
              <button type="button" className="ghost" onClick={() => { setOpen(false); setEditing(null); }}><RollingLabel>Cancel</RollingLabel></button>
              <button type="submit" disabled={saving}>{saving ? "Saving…" : <RollingLabel>{editing ? "Save changes" : "Register"}</RollingLabel>}</button>
            </div>
          </form>
        </Modal>
      )}

      {linkTarget && (
        <Modal title="Link guardian to learner" onClose={() => setLinkTarget(null)}>
          <form onSubmit={async (e) => {
            e.preventDefault();
            if (guardianAlreadyLinked) {
              setLinkError("This guardian is already linked to this learner. No change was made.");
              return;
            }
            if (linkNeedsConfirmation && !linkConfirmed) {
              setLinkError("Confirm the existing links before continuing.");
              return;
            }
            setLinkSaving(true);
            setLinkError(null);
            try {
              await api.post("/learners/guardian-links/", {
                learner: linkTarget.id,
                guardian: linkForm.guardian?.id,
                relationship: linkForm.relationship,
                is_primary: linkForm.is_primary,
                ...linkPermissionFields,
              });
              push(`Guardian ${selectedGuardian.guardian_name} linked to ${linkTarget.learner_name}.`, "success");
              setLinkTarget(null);
              reload();
            } catch (err) {
              setLinkError(err.message || "Could not link guardian.");
            } finally {
              setLinkSaving(false);
            }
          }}>
            {linkError && <div className="notice error" role="alert" style={{ marginBottom: "0.75rem" }}>{linkError}</div>}
            <p className="muted" style={{ marginBottom: "0.75rem" }}>
              Linking a guardian to <strong>{linkTarget.learner_name || linkTarget.username}</strong>.
            </p>
            <div className="form-grid">
              <div className="full">
                <PersonSearchSelect
                  label="Guardian"
                  endpoint="/guardians/"
                  placeholder="Type a name, username, guardian number or phone"
                  hint="Matches load as you type. Choose one to fill in the guardian details below."
                  nameKey="guardian_name"
                  identifierKey="guardian_number"
                  identifierLabel="Guardian number"
                  extraDetails={[
                    { label: "Username", key: "username" },
                    { label: "Phone", key: "phone" },
                    { label: "Email", key: "email" },
                  ]}
                  selected={linkForm.guardian}
                  onSelect={(guardian) => setLinkForm((form) => ({
                    ...form,
                    guardian,
                    relationship: guardian?.relationship_to_learner || form.relationship,
                  }))}
                />
              </div>
              {selectedGuardian && (
                <div className="full">
                  <LinkConfirmation
                    personLabel="guardian"
                    existingLabel="learner"
                    existingNames={existingGuardians}
                    otherNames={otherLearners}
                    pendingRequest={pendingRequest}
                    requestDetails={{
                      relationship: linkForm.relationship,
                      is_primary: linkForm.is_primary,
                      ...linkPermissionFields,
                    }}
                    onRequestDecided={requestDecided}
                    duplicate={guardianAlreadyLinked}
                    confirmed={linkConfirmed}
                    onConfirmedChange={setLinkConfirmed}
                  />
                </div>
              )}
              <FormField label="Relationship"><input value={linkForm.relationship} onChange={(e) => setLinkForm({ ...linkForm, relationship: e.target.value })} required /></FormField>
              <FormField label="Primary link" hint="Only one guardian can be primary. Choosing Yes replaces the earlier primary link.">
                <select value={linkForm.is_primary ? "yes" : "no"} onChange={(e) => setLinkForm({ ...linkForm, is_primary: e.target.value === "yes" })}>
                  <option value="yes">Yes</option>
                  <option value="no">No</option>
                </select>
              </FormField>
              <LinkPermissions
                value={linkForm}
                onChange={(key, checked) => setLinkForm((form) => ({ ...form, [key]: checked }))}
              />
            </div>
            <div className="form-actions">
              <button type="button" className="ghost" onClick={() => setLinkTarget(null)}><RollingLabel>Cancel</RollingLabel></button>
              <button type="submit" disabled={linkSaving || !linkForm.guardian || guardianAlreadyLinked || (linkNeedsConfirmation && !linkConfirmed)}>{linkSaving ? "Linking…" : <RollingLabel>Link guardian</RollingLabel>}</button>
            </div>
          </form>
        </Modal>
      )}

      {deleteTarget && (
        <Modal title="Delete learner" onClose={() => setDeleteTarget(null)}>
          <p style={{ marginBottom: "1rem" }}>
            Delete <strong>{deleteTarget.learner_name || deleteTarget.username}</strong>? This cannot be undone.
          </p>
          <div className="form-actions">
            <button type="button" className="ghost" onClick={() => setDeleteTarget(null)}><RollingLabel>Cancel</RollingLabel></button>
            <button type="button" className="danger" onClick={async () => { const row = deleteTarget; setDeleteTarget(null); await remove(row); }}><RollingLabel>Delete</RollingLabel></button>
          </div>
        </Modal>
      )}
    </section>
  );
}