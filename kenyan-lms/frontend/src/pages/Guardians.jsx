import { useState } from "react";
import { useList } from "../hooks/useApi";
import { api } from "../services/api";
import { useToast } from "../context/ToastContext";
import { useAuth } from "../context/AuthContext";
import { isAdmin } from "../utilities/roles";
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

export default function Guardians() {
  const { user } = useAuth();
  const canWrite = isAdmin(user);
  const { data, loading, error, reload } = useList("/guardians/");
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
    learner: null,
    relationship: "Parent",
    is_primary: true,
    can_view_academics: true,
    can_view_attendance: true,
    can_view_fees: false,
  });
  const [linkSaving, setLinkSaving] = useState(false);
  const [linkError, setLinkError] = useState(null);
  const [linkConfirmed, setLinkConfirmed] = useState(false);

  const selectedLearner = linkForm.learner;
  const { request: pendingRequest, clear: clearPendingRequest } = usePendingLinkRequest(
    linkTarget?.id, selectedLearner?.id
  );
  const existingLearners = linkTarget?.learner_names || [];
  const learnerAlreadyLinked = Boolean(selectedLearner && (
    (linkTarget?.learner_ids || []).some((id) => String(id) === String(selectedLearner.id))
    || existingLearners.some(
      (name) => String(name).toLowerCase() === String(selectedLearner.learner_name || "").toLowerCase()
    )
  ));
  const otherGuardians = selectedLearner?.guardian_names || [];
  const linkNeedsConfirmation = !learnerAlreadyLinked && Boolean(
    existingLearners.length || otherGuardians.length || pendingRequest
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
    setForm({ username: "", first_name: "", last_name: "", email: "", guardian_number: "", phone: "", occupation: "", relationship_to_learner: "", preferred_language: "en", receive_sms: true });
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
      guardian_number: row.guardian_number || "",
      phone: row.phone || "",
      occupation: row.occupation || "",
      relationship_to_learner: row.relationship_to_learner || "",
      preferred_language: row.preferred_language || "en",
      receive_sms: row.receive_sms !== false,
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
        await api.patch(`/guardians/${editing.id}/`, form);
        push("Guardian updated.", "success");
      } else {
        await api.post("/guardians/", form);
        push("Guardian created.", "success");
      }
      setOpen(false);
      setEditing(null);
      reload();
    } catch (err) {
      setFormError(err.message || "Could not save guardian.");
    } finally {
      setSaving(false);
    }
  }

  async function remove(row) {
    try {
      await api.del(`/guardians/${row.id}/`);
      push("Guardian deleted.", "success");
      reload();
    } catch (err) { push(err.message, "error"); }
  }

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">Parents & guardians</div>
          <h1>Guardians</h1>
        </div>
        <div className="actions">
          {canWrite && <button onClick={startCreate}><RollingLabel>New guardian</RollingLabel></button>}
        </div>
      </div>

      <TableToolbar title="guardians" controls={controls} onRefresh={reload} />

      <DataTable
        columns={[
          { key: "guardian_name", label: "Name" },
          { key: "guardian_number", label: "Guardian no.", render: (r) => <span className="mono">{r.guardian_number || "—"}</span> },
          { key: "institution_code", label: "School code", render: (r) => r.institution_code || "—" },
          { key: "learner_names", label: "Linked learners", render: (r) => {
            const names = r.learner_names || [];
            return names.length
              ? <><span className="tag good">Linked</span> {names.join(", ")}</>
              : <span className="tag warn">Not linked</span>;
          } },
          { key: "email", label: "Email" },
          { key: "phone", label: "Phone" },
          { key: "relationship_to_learner", label: "Relationship" },
          { key: "_actions", label: "Actions", render: (r) => canWrite && (
            <div className="row-actions">
              <button className="small" onClick={() => { setLinkTarget(r); setLinkForm({ learner: null, relationship: "Parent", is_primary: true, can_view_academics: true, can_view_attendance: true, can_view_fees: false }); setLinkError(null); setLinkConfirmed(false); }}>
                <RollingLabel>{(r.learner_names || []).length ? "Add learner" : "Link learner"}</RollingLabel>
              </button>
              <button className="ghost small" onClick={() => startEdit(r)}><RollingLabel>Edit</RollingLabel></button>
              <button className="ghost small danger" onClick={() => setDeleteTarget(r)}><RollingLabel>Delete</RollingLabel></button>
            </div>
          ) },
        ]}
        rows={controls.visibleRows}
        loading={loading}
        error={error}
        emptyTitle="No guardians yet"
        emptyHint="Create guardian accounts and link them to learners."
      />

      {!loading && !error && <TablePagination controls={controls} />}

      {open && (
        <Modal title={editing ? "Edit guardian" : "New guardian"} onClose={() => { setOpen(false); setEditing(null); }}>
          <form onSubmit={save}>
            {formError && <div className="notice error" role="alert" style={{ marginBottom: "0.75rem" }}>{formError}</div>}
            <div className="form-grid">
              {!editing && (
                <>
                  <FormField label="Username" hint="Leave blank to generate from the name."><input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} /></FormField>
                  <FormField label="First name"><input value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} required /></FormField>
                  <FormField label="Last name"><input value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} required /></FormField>
                </>
              )}
              {editing && (
                <>
                  <FormField label="Username"><input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} /></FormField>
                  <FormField label="First name"><input value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} required /></FormField>
                  <FormField label="Last name"><input value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} required /></FormField>
                </>
              )}
              <FormField label="Email"><input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></FormField>
              <FormField label="Guardian number" hint="Leave blank to generate GD-SCHOOL-001."><input value={form.guardian_number} onChange={(e) => setForm({ ...form, guardian_number: e.target.value })} /></FormField>
              <FormField label="Phone"><input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></FormField>
              <FormField label="Relationship"><input value={form.relationship_to_learner} onChange={(e) => setForm({ ...form, relationship_to_learner: e.target.value })} /></FormField>
              <FormField label="Occupation"><input value={form.occupation} onChange={(e) => setForm({ ...form, occupation: e.target.value })} /></FormField>
              <FormField label="Preferred language"><input value={form.preferred_language} onChange={(e) => setForm({ ...form, preferred_language: e.target.value })} /></FormField>
            </div>
            <div className="form-actions">
              <button type="button" className="ghost" onClick={() => { setOpen(false); setEditing(null); }}><RollingLabel>Cancel</RollingLabel></button>
              <button type="submit" disabled={saving}>{saving ? "Saving…" : <RollingLabel>{editing ? "Save changes" : "Create"}</RollingLabel>}</button>
            </div>
          </form>
        </Modal>
      )}

      {linkTarget && (
        <Modal title="Link learner to guardian" onClose={() => setLinkTarget(null)}>
          <form onSubmit={async (e) => {
            e.preventDefault();
            if (learnerAlreadyLinked) {
              setLinkError("This learner is already linked to this guardian. No change was made.");
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
                learner: linkForm.learner?.id,
                guardian: linkTarget.id,
                relationship: linkForm.relationship,
                is_primary: linkForm.is_primary,
                ...linkPermissionFields,
              });
              push(`Learner ${selectedLearner.learner_name} linked to guardian ${linkTarget.guardian_name}.`, "success");
              setLinkTarget(null);
              reload();
            } catch (err) {
              setLinkError(err.message || "Could not link learner.");
            } finally {
              setLinkSaving(false);
            }
          }}>
            {linkError && <div className="notice error" role="alert" style={{ marginBottom: "0.75rem" }}>{linkError}</div>}
            <p className="muted" style={{ marginBottom: "0.75rem" }}>
              Linking a learner to <strong>{linkTarget.guardian_name || linkTarget.username}</strong>.
            </p>
            <div className="form-grid">
              <div className="full">
                <PersonSearchSelect
                  label="Learner"
                  endpoint="/learners/"
                  placeholder="Type a name, username or admission number"
                  hint="Matches load as you type. Choose one to fill in the learner details below."
                  nameKey="learner_name"
                  identifierKey="admission_number"
                  identifierLabel="Admission number"
                  extraDetails={[
                    { label: "Username", key: "username" },
                    { label: "Class", key: "class_name" },
                    { label: "Email", key: "email" },
                  ]}
                  selected={linkForm.learner}
                  onSelect={(learner) => setLinkForm((form) => ({ ...form, learner }))}
                />
              </div>
              {selectedLearner && (
                <div className="full">
                  <LinkConfirmation
                    personLabel="learner"
                    existingLabel="guardian"
                    existingNames={existingLearners}
                    otherNames={otherGuardians}
                    pendingRequest={pendingRequest}
                    requestDetails={{
                      relationship: linkForm.relationship,
                      is_primary: linkForm.is_primary,
                      ...linkPermissionFields,
                    }}
                    onRequestDecided={requestDecided}
                    duplicate={learnerAlreadyLinked}
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
              <button type="submit" disabled={linkSaving || !linkForm.learner || learnerAlreadyLinked || (linkNeedsConfirmation && !linkConfirmed)}>{linkSaving ? "Linking…" : <RollingLabel>Link learner</RollingLabel>}</button>
            </div>
          </form>
        </Modal>
      )}

      {deleteTarget && (
        <Modal title="Delete guardian" onClose={() => setDeleteTarget(null)}>
          <p style={{ marginBottom: "1rem" }}>
            Delete <strong>{deleteTarget.guardian_name || deleteTarget.username}</strong>? This cannot be undone.
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