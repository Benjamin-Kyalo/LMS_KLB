export default function Modal({ title, onClose, children }) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true" aria-label={title}>
        <div className="page-head" style={{ marginBottom: "0.9rem", paddingBottom: "0.5rem" }}>
          <h2 style={{ margin: 0 }}>{title}</h2>
          <button type="button" className="ghost small" onClick={onClose} aria-label="Close dialog">Close</button>
        </div>
        {children}
      </div>
    </div>
  );
}
