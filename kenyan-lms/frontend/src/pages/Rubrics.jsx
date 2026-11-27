import { useEffect, useState } from "react";
import { ClipboardCheck, ListChecks, MessageSquareText, Trash2 } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { useList } from "../hooks/useApi";
import useTableControls from "../hooks/useTableControls";
import { api, listAll } from "../services/api";
import { canWriteTeaching, isSuperAdmin } from "../utilities/roles";
import DataTable from "../components/DataTable";
import FormField from "../components/FormField";
import Modal from "../components/Modal";
import RollingLabel from "../components/RollingLabel";
import { DialogLead, DialogSection } from "../components/DialogParts";
import { TablePagination, TableToolbar } from "../components/TableTools";

const RUBRICS = "/curriculum/rubrics/";
const LEVELS = "/curriculum/rubric-levels/";
const CRITERIA = "/curriculum/rubric-criteria/";
const COMMENTS = "/curriculum/feedback-comments/";

const TYPE_LABELS = {
  rubric: "rubric",
  level: "achievement band",
  criterion: "criterion",
  comment: "feedback comment",
};

function blankFor(type, rubricId) {
  if (type === "rubric") return { name: "", description: "", institution: "" };
  if (type === "level") {
    return { rubric: rubricId, name: "", min_score: "0", max_score: "100", sequence: 1, description: "" };
  }
  if (type === "criterion") {
    return { rubric: rubricId, name: "", max_score: "10", sequence: 1, description: "" };
  }
  return { category: "", text: "", institution: "" };
}

function valuesFromRow(type, row) {
  if (!row) return blankFor(type);
  const common = { ...row };
  if (type === "level" || type === "criterion") {
    common.rubric = typeof row.rubric === "object" ? row.rubric?.id : row.rubric;
  }
  return common;
}

function nameOf(row) {
  return row?.name || row?.text || "this record";
}

export default function Rubrics() {
  const { user } = useAuth();
  const { push } = useToast();
  const rubrics = useList(RUBRICS);
  const levels = useList(LEVELS);
  const criteria = useList(CRITERIA);
  const comments = useList(COMMENTS);
  const controls = useTableControls(rubrics.data);
  const [institutions, setInstitutions] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [dialog, setDialog] = useState(null);
  const [form, setForm] = useState({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const canWrite = canWriteTeaching(user);
  const platform = isSuperAdmin(user);

  useEffect(() => {
    if (!platform) return undefined;
    let active = true;
    listAll("/institutions/")
      .then((rows) => { if (active) setInstitutions(rows); })
      .catch(() => { if (active) setInstitutions([]); });
    return () => { active = false; };
  }, [platform]);

  const selected = rubrics.data.find((row) => String(row.id) === String(selectedId))
    || rubrics.data[0] || null;
  const selectedKey = selected?.id || "";
  const selectedLevels = levels.data.filter(
    (row) => String(typeof row.rubric === "object" ? row.rubric?.id : row.rubric) === String(selectedKey),
  );
  const selectedCriteria = criteria.data.filter(
    (row) => String(typeof row.rubric === "object" ? row.rubric?.id : row.rubric) === String(selectedKey),
  );

  function update(name, value) {
    setForm((previous) => ({ ...previous, [name]: value }));
  }

  function openForm(type, row = null) {
    setForm(valuesFromRow(type, row));
    if (type === "level" || type === "criterion") {
      update("rubric", selectedKey);
    }
    setError(null);
    setDialog({ type, row });
  }

  function openDelete(type, row) {
    setError(null);
    setDialog({ type: "delete", targetType: type, row });
  }

  function endpointFor(type) {
    return { rubric: RUBRICS, level: LEVELS, criterion: CRITERIA, comment: COMMENTS }[type];
  }

  function payloadFor(type) {
    if (type === "rubric") {
      const payload = { name: String(form.name || "").trim(), description: form.description || "" };
      if (platform && form.institution) payload.institution = form.institution;
      return payload;
    }
    if (type === "level") {
      return {
        rubric: form.rubric || selectedKey,
        name: String(form.name || "").trim(),
        description: form.description || "",
        min_score: Number(form.min_score),
        max_score: Number(form.max_score),
        sequence: Number(form.sequence) || 1,
      };
    }
    if (type === "criterion") {
      return {
        rubric: form.rubric || selectedKey,
        name: String(form.name || "").trim(),
        description: form.description || "",
        max_score: Number(form.max_score),
        sequence: Number(form.sequence) || 1,
      };
    }
    const payload = { category: form.category || "", text: String(form.text || "").trim() };
    if (platform && form.institution) payload.institution = form.institution;
    return payload;
  }

  function validate(type) {
    if (!String(form.name || form.text || "").trim()) {
      return `Enter a ${TYPE_LABELS[type]} name before saving.`;
    }
    if (type === "level") {
      if (Number(form.min_score) < 0 || Number(form.max_score) > 100) {
        return "Achievement bands must stay between 0 and 100 percent.";
      }
      if (Number(form.min_score) > Number(form.max_score)) {
        return "The minimum cannot be higher than the maximum.";
      }
    }
    if ((type === "level" || type === "criterion") && Number(form.max_score) <= 0) {
      return "The maximum score must be greater than zero.";
    }
    return null;
  }

  async function save(event) {
    event.preventDefault();
    const type = dialog.type;
    const problem = validate(type);
    if (problem) {
      setError(problem);
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const endpoint = endpointFor(type);
      const payload = payloadFor(type);
      if (dialog.row) await api.patch(`${endpoint}${dialog.row.id}/`, payload);
      else await api.post(endpoint, payload);
      setDialog(null);
      await Promise.all([rubrics.reload(), levels.reload(), criteria.reload(), comments.reload()]);
      push(`Rubric ${TYPE_LABELS[type]} saved.`, "success");
    } catch (err) {
      setError(err.message || "The change could not be saved. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    const { targetType, row } = dialog;
    setBusy(true);
    setError(null);
    try {
      await api.del(`${endpointFor(targetType)}${row.id}/`);
      setDialog(null);
      if (targetType === "rubric" && String(selectedId) === String(row.id)) setSelectedId(null);
      await Promise.all([rubrics.reload(), levels.reload(), criteria.reload(), comments.reload()]);
      push("Rubric record deleted.", "success");
    } catch (err) {
      setError(err.message || "The record could not be deleted.");
    } finally {
      setBusy(false);
    }
  }

  const loading = rubrics.loading || levels.loading || criteria.loading || comments.loading;
  const loadError = rubrics.error || levels.error || criteria.error || comments.error;

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">Assessment design</div>
          <h1>Rubrics &amp; feedback</h1>
          <p>Build achievement bands and scored criteria once, then reuse them across assignments.</p>
        </div>
        <div className="actions">
          {canWrite && (
            <button onClick={() => openForm("rubric")}><RollingLabel>New rubric</RollingLabel></button>
          )}
        </div>
      </div>

      <div className="notice info dialog-error" role="note">
        Criteria carry the marks; achievement bands use percentages of the assignment total. Feedback stays
        private until a teacher publishes it to the learner and permitted guardians. Changes here are recorded
        in the audit history.
      </div>

      <TableToolbar title="rubrics" controls={controls} onRefresh={() => Promise.all([
        rubrics.reload(), levels.reload(), criteria.reload(), comments.reload(),
      ])} />

      <DataTable
        columns={[
          { key: "name", label: "Rubric" },
          { key: "institution_code", label: "Scope", render: (r) => r.institution_code ? <span className="mono">{r.institution_code}</span> : "Global template" },
          { key: "levels", label: "Bands", render: (r) => r.levels?.length ?? 0 },
          { key: "criteria", label: "Criteria", render: (r) => r.criteria?.length ?? 0 },
          { key: "_actions", label: "Actions", render: (r) => (
            <div className="row-actions">
              <button
                className="ghost small"
                aria-label={`Manage ${r.name}`}
                onClick={() => setSelectedId(r.id)}
              >
                <RollingLabel>Manage</RollingLabel>
              </button>
              {canWrite && (
                <>
                  <button className="ghost small" aria-label={`Edit ${r.name}`} onClick={() => openForm("rubric", r)}>
                    <RollingLabel>Edit</RollingLabel>
                  </button>
                  <button className="ghost small danger" aria-label={`Delete ${r.name}`} onClick={() => openDelete("rubric", r)}>
                    <RollingLabel>Delete</RollingLabel>
                  </button>
                </>
              )}
            </div>
          ) },
        ]}
        rows={controls.visibleRows}
        loading={loading}
        error={loadError}
        emptyTitle="No rubrics yet"
        emptyHint={canWrite ? "Create a rubric to add achievement bands and criteria." : "A teacher will publish the school's rubrics here."}
      />
      {!loading && !loadError && <TablePagination controls={controls} />}

      {selected && (
        <div className="two-column" style={{ marginTop: "1.5rem" }}>
          <section className="panel panel-pad">
            <div className="page-head" style={{ marginBottom: "0.8rem" }}>
              <div>
                <div className="overline">{selected.institution_code || "Global template"}</div>
                <h2>{selected.name}</h2>
              </div>
              {canWrite && (
                <div className="actions">
                  <button className="secondary small" onClick={() => openForm("level")}><RollingLabel>New band</RollingLabel></button>
                  <button className="small" onClick={() => openForm("criterion")}><RollingLabel>New criterion</RollingLabel></button>
                </div>
              )}
            </div>
            {selected.description && <p className="muted">{selected.description}</p>}

            <h3>Achievement bands</h3>
            <DataTable
              columns={[
                { key: "name", label: "Band" },
                { key: "range", label: "Percentage", render: (r) => `${r.min_score}–${r.max_score}%` },
                { key: "_actions", label: "Actions", render: (r) => canWrite ? (
                  <div className="row-actions">
                    <button className="ghost small" aria-label={`Edit band ${r.name}`} onClick={() => openForm("level", r)}><RollingLabel>Edit</RollingLabel></button>
                    <button className="ghost small danger" aria-label={`Delete band ${r.name}`} onClick={() => openDelete("level", r)}><RollingLabel>Delete</RollingLabel></button>
                  </div>
                ) : "—" },
              ]}
              rows={selectedLevels}
              loading={levels.loading}
              error={levels.error}
              emptyTitle="No achievement bands"
              emptyHint="Add bands such as Beginning, Developing and Achieving."
            />

            <h3 style={{ marginTop: "1.25rem" }}>Scored criteria</h3>
            <DataTable
              columns={[
                { key: "name", label: "Criterion" },
                { key: "max_score", label: "Maximum" },
                { key: "_actions", label: "Actions", render: (r) => canWrite ? (
                  <div className="row-actions">
                    <button className="ghost small" aria-label={`Edit criterion ${r.name}`} onClick={() => openForm("criterion", r)}><RollingLabel>Edit</RollingLabel></button>
                    <button className="ghost small danger" aria-label={`Delete criterion ${r.name}`} onClick={() => openDelete("criterion", r)}><RollingLabel>Delete</RollingLabel></button>
                  </div>
                ) : "—" },
              ]}
              rows={selectedCriteria}
              loading={criteria.loading}
              error={criteria.error}
              emptyTitle="No criteria"
              emptyHint="Each criterion becomes one row on the teacher's marking grid."
            />
          </section>

          <section className="panel panel-pad">
            <div className="page-head" style={{ marginBottom: "0.8rem" }}>
              <div>
                <div className="overline">Comment bank</div>
                <h2>Reusable feedback</h2>
              </div>
              {canWrite && (
                <button className="secondary small" onClick={() => openForm("comment")}><RollingLabel>New comment</RollingLabel></button>
              )}
            </div>
            <p className="muted">Keep written feedback short, specific and kind. Teachers choose phrases here while marking.</p>
            <DataTable
              columns={[
                { key: "text", label: "Comment" },
                { key: "category", label: "Category", render: (r) => r.category || "General" },
                { key: "_actions", label: "Actions", render: (r) => canWrite ? (
                  <div className="row-actions">
                    <button className="ghost small" aria-label={`Edit comment ${r.text}`} onClick={() => openForm("comment", r)}><RollingLabel>Edit</RollingLabel></button>
                    <button className="ghost small danger" aria-label={`Delete comment ${r.text}`} onClick={() => openDelete("comment", r)}><RollingLabel>Delete</RollingLabel></button>
                  </div>
                ) : "—" },
              ]}
              rows={comments.data}
              loading={comments.loading}
              error={comments.error}
              emptyTitle="No saved comments"
              emptyHint="Add a phrase you use often to speed up marking."
            />
          </section>
        </div>
      )}

      {dialog && dialog.type !== "delete" && (
        <Modal
          title={`${dialog.row ? "Edit" : "New"} ${TYPE_LABELS[dialog.type]}`}
          onClose={() => setDialog(null)}
        >
          <form onSubmit={save}>
            <DialogLead
              icon={{ rubric: ClipboardCheck, level: ListChecks, criterion: ListChecks, comment: MessageSquareText }[dialog.type]}
              kicker="Rubric builder"
            >
              {dialog.type === "comment"
                ? "Saved phrases keep feedback consistent across classes."
                : "These settings define the grid teachers use when marking an assignment."}
            </DialogLead>
            {error && <div className="notice error dialog-error" role="alert">{error}</div>}
            <DialogSection title="Details">
              <div className="form-grid">
                {dialog.type === "rubric" && (
                  <>
                    <FormField label="Rubric name">
                      <input value={form.name || ""} onChange={(e) => update("name", e.target.value)} required />
                    </FormField>
                    <FormField label="Description" full>
                      <textarea rows={3} value={form.description || ""} onChange={(e) => update("description", e.target.value)} />
                    </FormField>
                    {platform && (
                      <FormField label="Institution" hint="Leave blank for a global template.">
                        <select value={form.institution || ""} onChange={(e) => update("institution", e.target.value)}>
                          <option value="">— global template —</option>
                          {institutions.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                        </select>
                      </FormField>
                    )}
                  </>
                )}
                {(dialog.type === "level" || dialog.type === "criterion") && (
                  <>
                    <FormField label="Rubric">
                      <select value={form.rubric || selectedKey} onChange={(e) => update("rubric", e.target.value)} required>
                        <option value={selectedKey}>{selected?.name || "Choose a rubric"}</option>
                      </select>
                    </FormField>
                    <FormField label={dialog.type === "level" ? "Band name" : "Criterion name"}>
                      <input value={form.name || ""} onChange={(e) => update("name", e.target.value)} required />
                    </FormField>
                    {dialog.type === "level" ? (
                      <>
                        <FormField label="Minimum percentage">
                          <input type="number" min="0" max="100" step="0.01" value={form.min_score ?? ""} onChange={(e) => update("min_score", e.target.value)} required />
                        </FormField>
                        <FormField label="Maximum percentage">
                          <input type="number" min="0" max="100" step="0.01" value={form.max_score ?? ""} onChange={(e) => update("max_score", e.target.value)} required />
                        </FormField>
                      </>
                    ) : (
                      <FormField label="Maximum score">
                        <input type="number" min="0.01" step="0.01" value={form.max_score ?? ""} onChange={(e) => update("max_score", e.target.value)} required />
                      </FormField>
                    )}
                    <FormField label="Order">
                      <input type="number" min="1" value={form.sequence ?? 1} onChange={(e) => update("sequence", e.target.value)} />
                    </FormField>
                    <FormField label="Description" full>
                      <textarea rows={3} value={form.description || ""} onChange={(e) => update("description", e.target.value)} />
                    </FormField>
                  </>
                )}
                {dialog.type === "comment" && (
                  <>
                    <FormField label="Category">
                      <input value={form.category || ""} onChange={(e) => update("category", e.target.value)} placeholder="e.g. Writing" />
                    </FormField>
                    <FormField label="Comment" full>
                      <textarea rows={4} value={form.text || ""} onChange={(e) => update("text", e.target.value)} required />
                    </FormField>
                    {platform && (
                      <FormField label="Institution" hint="Leave blank for a global comment.">
                        <select value={form.institution || ""} onChange={(e) => update("institution", e.target.value)}>
                          <option value="">— global comment —</option>
                          {institutions.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                        </select>
                      </FormField>
                    )}
                  </>
                )}
              </div>
            </DialogSection>
            <div className="dialog-actions">
              <button type="button" className="ghost" onClick={() => setDialog(null)}><RollingLabel>Cancel</RollingLabel></button>
              <button type="submit" disabled={busy} aria-busy={busy || undefined}>
                {busy ? "Saving…" : <RollingLabel>{dialog.row ? "Save changes" : `Create ${TYPE_LABELS[dialog.type]}`}</RollingLabel>}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {dialog?.type === "delete" && (
        <Modal title={`Delete ${TYPE_LABELS[dialog.targetType]}`} onClose={() => setDialog(null)}>
          <DialogLead icon={Trash2} tone="bad" kicker="Confirm deletion">
            Delete <strong>{nameOf(dialog.row)}</strong>? Existing grades keep their own snapshot, but this
            definition will no longer be available for new assignments.
          </DialogLead>
          {error && <div className="notice error dialog-error" role="alert">{error}</div>}
          <div className="dialog-actions">
            <button type="button" className="ghost" onClick={() => setDialog(null)}><RollingLabel>Cancel</RollingLabel></button>
            <button type="button" className="danger" onClick={remove} disabled={busy} aria-busy={busy || undefined}>
              {busy ? "Deleting…" : <RollingLabel>Delete {TYPE_LABELS[dialog.targetType]}</RollingLabel>}
            </button>
          </div>
        </Modal>
      )}
    </section>
  );
}
