// Shared building blocks for focused administrative dialogs. The visible
// heading, explanation and action labels stay present while a request runs;
// only the button label changes to a progress state.
export function DialogLead({ icon: Icon, kicker, tone = "info", children }) {
  return (
    <div className="dialog-lead">
      <span className={`dialog-lead-icon ${tone}`} aria-hidden="true">
        <Icon size={20} />
      </span>
      <div>
        {kicker && <div className="dialog-kicker">{kicker}</div>}
        <p>{children}</p>
      </div>
    </div>
  );
}

export function DialogSection({ title, hint, children }) {
  return (
    <section className="dialog-section">
      <h3>{title}</h3>
      {hint && <p className="muted">{hint}</p>}
      {children}
    </section>
  );
}
