import { createContext, useCallback, useContext, useState } from "react";

const ToastContext = createContext(null);

function noticeKind(kind) {
  if (kind === "warning") return "warn";
  return ["error", "warn", "success", "info"].includes(kind) ? kind : "info";
}

function noticeRole(kind) {
  return ["error", "warn", "warning"].includes(kind) ? "alert" : "status";
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const push = useCallback((message, kind = "info") => {
    const id = Date.now() + Math.random();
    setToasts((t) => [...t, { id, message, kind }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4000);
  }, []);

  return (
    <ToastContext.Provider value={{ push }}>
      {children}
      <div className="toast-stack">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`notice ${noticeKind(t.kind)}`}
            role={noticeRole(t.kind)}
          >
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  return useContext(ToastContext);
}
