import { cloneElement, isValidElement, useId } from "react";

export default function FormField({ label, hint, error, children, full }) {
  const generatedId = useId();
  const isControl = isValidElement(children);
  const childId = isControl && children.props.id ? children.props.id : generatedId;
  const hintId = `${generatedId}-hint`;
  const errorId = `${generatedId}-error`;
  const required = isControl && Boolean(children.props.required);
  const describedBy = [hint && hintId, error && errorId].filter(Boolean).join(" ") || undefined;
  const field = isControl
    ? cloneElement(children, {
        id: childId,
        ...(describedBy ? { "aria-describedby": describedBy } : {}),
        ...(error ? { "aria-invalid": true } : {}),
        ...(required ? { required: true } : {}),
      })
    : children;

  return (
    <div className={full ? "full" : undefined}>
      <label htmlFor={childId}>
        {label}
        {required && <span className="required-mark" aria-hidden="true" />}
      </label>
      {hint && <p id={hintId} className="muted" style={{ fontSize: "0.78rem", margin: "0 0 0.3rem" }}>{hint}</p>}
      {field}
      {error && (
        <p
          id={errorId}
          role="alert"
          className="muted"
          style={{ color: "var(--bad)", fontSize: "0.8rem", margin: "0.25rem 0 0" }}
        >
          {error}
        </p>
      )}
    </div>
  );
}
