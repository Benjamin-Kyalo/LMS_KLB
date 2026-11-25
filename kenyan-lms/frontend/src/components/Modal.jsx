import { createPortal } from "react-dom";
import { useEffect, useRef } from "react";
import RollingLabel from "./RollingLabel";

export default function Modal({ title, onClose, children }) {
  const dialogRef = useRef(null);

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const dialog = dialogRef.current;
    const focusable = dialog
      ? Array.from(dialog.querySelectorAll("button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])"))
      : [];
    focusable[0]?.focus();

    function onKeyDown(event) {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
        return;
      }
      if (event.key !== "Tab" || focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    dialog?.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      dialog?.removeEventListener("keydown", onKeyDown);
    };
  }, [onClose]);

  if (typeof document === "undefined") return null;
  return createPortal(
    <div className="modal-backdrop" onClick={onClose}>
      <div ref={dialogRef} className="modal" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true" aria-label={title}>
        <div className="page-head" style={{ marginBottom: "0.9rem", paddingBottom: "0.5rem" }}>
          <h2 style={{ margin: 0 }}>{title}</h2>
          <button type="button" className="ghost small" onClick={onClose} aria-label="Close dialog">
            <RollingLabel>Close</RollingLabel>
          </button>
        </div>
        {children}
      </div>
    </div>,
    document.body,
  );
}
