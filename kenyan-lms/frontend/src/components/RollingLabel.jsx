/**
 * A label that rolls into place on hover or keyboard focus.
 *
 * The first span is the real, always-present accessible name. The duplicate is
 * decorative and hidden from assistive technology, so animation never changes
 * what a button or link means.
 */
export default function RollingLabel({ children, className = "" }) {
  return (
    <span className={`rolling-label ${className}`.trim()}>
      <span className="rolling-label-static">{children}</span>
      <span className="rolling-label-motion" aria-hidden="true">{children}</span>
    </span>
  );
}
