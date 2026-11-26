const PERMISSIONS = [
  {
    key: "can_view_academics",
    label: "Academic records",
    description: "Grades, assessments and learner reports.",
  },
  {
    key: "can_view_attendance",
    label: "Attendance",
    description: "Daily attendance and absence history.",
  },
  {
    key: "can_view_fees",
    label: "Fee information",
    description: "Balances and payment history. Off by default.",
  },
];

/** Access choices stored on the guardian/learner link, never on the account. */
export default function LinkPermissions({ value = {}, onChange }) {
  return (
    <fieldset className="form-section full link-permissions">
      <legend>Guardian access</legend>
      <p className="muted">Choose what this guardian may see for this learner.</p>
      <div className="check-grid">
        {PERMISSIONS.map(({ key, label, description }) => (
          <label className="checkline" key={key}>
            <input
              type="checkbox"
              checked={Boolean(value[key])}
              onChange={(event) => onChange(key, event.target.checked)}
            />
            <span>
              <strong>{label}</strong>
              <small>{description}</small>
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
