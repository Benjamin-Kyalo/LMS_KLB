import { cloneElement, isValidElement, useId } from "react";

export default function FormField({ label, hint, error, children, full }) {
  const generatedId = useId();
  const childId = isValidElement(children) && children.props.id ? children.props.id : generatedId;
  const hintId = `${generatedId}-hint`;
  const field = isValidElement(children)
    ? cloneElement(children, {
        id: childId,
        ...(hint ? { "aria-describedby": hintId } : {}),
      })
    : children;

  return (
    <div className={full ? "full" : undefined}>
      <label htmlFor={childId}>{label}</label>
      {hint && <p id={hintId} className="muted" style={{ fontSize: "0.78rem", margin: "0 0 0.3rem" }}>{hint}</p>}
      {field}
      {error && <p className="muted" style={{ color: "var(--bad)", fontSize: "0.8rem", margin: "0.25rem 0 0" }}>{error}</p>}
    </div>
  );
}
