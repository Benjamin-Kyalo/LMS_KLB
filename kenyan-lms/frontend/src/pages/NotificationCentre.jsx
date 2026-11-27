import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useList, useResource } from "../hooks/useApi";
import { api } from "../services/api";
import { useToast } from "../context/ToastContext";
import { useSiteContent } from "../context/SiteContentContext";
import DataTable from "../components/DataTable";
import Modal from "../components/Modal";
import RollingLabel from "../components/RollingLabel";
import { TableToolbar, TablePagination } from "../components/TableTools";
import useTableControls from "../hooks/useTableControls";
import { formatDateTime } from "../utilities/format";

const NOTIFICATION_TYPES = [
  ["GENERAL", "General"],
  ["ACADEMIC", "Academic"],
  ["ATTENDANCE", "Attendance"],
  ["MESSAGE", "Message"],
  ["SYSTEM", "System"],
];

function readableError(value, fallback) {
  const text = typeof value === "string" ? value.trim() : "";
  if (!text || /^[\[{]/.test(text) || /<\/?[A-Za-z][^>]*>/.test(text)) return fallback;
  return text === "[object Object]" ? fallback : text;
}

export default function NotificationCentre() {
  const { push } = useToast();
  const { content } = useSiteContent();
  const messages = content.messages || {};
  const somethingWrong = messages.errors?.somethingWrong
    || "We could not complete that action. Try again, or contact support if the problem continues. Include the reference number shown on this page.";
  const pageIntroduction = messages.pageIntroductions?.notifications
    || "Keep track of important updates and messages relevant to your account.";
  const emptyState = messages.emptyStates?.notifications || {
    title: "You're all caught up",
    message: "Important updates will appear here when they arrive.",
  };
  const searchHint = messages.emptyStates?.resources?.message
    || "Try changing your search or exploring another category.";
  const notifications = useList("/communications/notifications/");
  const unread = useResource("/communications/notifications/unread-count/");
  const preferences = useList("/communications/preferences/");
  const controls = useTableControls(notifications.data);
  const [selected, setSelected] = useState(null);
  const [busy, setBusy] = useState(false);
  const [prefBusy, setPrefBusy] = useState(false);
  const savedPreferences = preferences.data?.[0] || null;
  const [prefs, setPrefs] = useState({
    in_app: true, email: true, sms: false, types: [],
  });

  useEffect(() => {
    if (!savedPreferences) return;
    setPrefs({
      in_app: savedPreferences.in_app !== false,
      email: savedPreferences.email !== false,
      sms: Boolean(savedPreferences.sms),
      types: Array.isArray(savedPreferences.types) ? savedPreferences.types : [],
    });
  }, [savedPreferences]);

  async function act(path, message) {
    setBusy(true);
    try {
      await api.post(path, {});
      push(message, "success");
      notifications.reload();
      unread.reload();
    } catch (err) {
      push(readableError(err?.message, somethingWrong), "error");
    } finally {
      setBusy(false);
    }
  }

  function toggleType(code) {
    setPrefs((current) => ({
      ...current,
      types: current.types.includes(code)
        ? current.types.filter((item) => item !== code)
        : [...current.types, code],
    }));
  }

  async function savePreferences(event) {
    event.preventDefault();
    setPrefBusy(true);
    try {
      const body = {
        in_app: prefs.in_app,
        email: prefs.email,
        sms: prefs.sms,
        types: prefs.types,
      };
      if (savedPreferences?.id) {
        await api.patch(`/communications/preferences/${savedPreferences.id}/`, body);
      } else {
        await api.post("/communications/preferences/", body);
      }
      push("Notification preferences saved.", "success");
      preferences.reload();
    } catch (err) {
      push(readableError(err?.message, somethingWrong), "error");
    } finally {
      setPrefBusy(false);
    }
  }

  const rows = controls.visibleRows;
  const loadError = notifications.error || unread.error || preferences.error;

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">Your inbox</div>
          <h1>Notifications</h1>
          <p className="muted">
            {pageIntroduction} {unread.data?.count ?? 0} unread alert(s). School events appear here automatically.
          </p>
        </div>
        <div className="actions">
          <button
            className="secondary"
            disabled={busy || !unread.data?.count}
            aria-busy={busy || undefined}
            onClick={() => act("/communications/notifications/mark-all-read/", "All notifications marked as read.")}
          >
            {busy ? "Updating…" : <RollingLabel>Mark all as read</RollingLabel>}
          </button>
          <Link className="button-link ghost" to="/portal/communications">
            <RollingLabel>Messages</RollingLabel>
          </Link>
        </div>
      </div>

      {loadError && (
        <div className="notice error" role="alert">
          {readableError(loadError, somethingWrong)}
        </div>
      )}

      <div className="panel panel-pad" style={{ marginBottom: "1rem" }}>
        <h2 style={{ marginTop: 0 }}>How alerts work</h2>
        <p className="muted">
          Notifications are created by school workflows such as guardian links, fee payments and
          early-warning reviews. They cannot be sent by other users through this page. You can
          choose which events reach you in your notification preferences.
        </p>
      </div>

      <div className="panel panel-pad" style={{ marginBottom: "1rem" }}>
        <h2 style={{ marginTop: 0 }}>Notification preferences</h2>
        <p className="muted">
          An empty type selection allows every event. Choosing types limits inbox alerts to those
          events; email delivery follows the same choice.
        </p>
        <form onSubmit={savePreferences}>
          <div className="form-grid">
            <label className="checkline">
              <input
                type="checkbox"
                checked={prefs.in_app}
                onChange={(event) => setPrefs({ ...prefs, in_app: event.target.checked })}
              />
              In-app inbox
            </label>
            <label className="checkline">
              <input
                type="checkbox"
                checked={prefs.email}
                onChange={(event) => setPrefs({ ...prefs, email: event.target.checked })}
              />
              Email alerts
            </label>
            <label className="checkline">
              <input
                type="checkbox"
                checked={prefs.sms}
                onChange={(event) => setPrefs({ ...prefs, sms: event.target.checked })}
              />
              SMS alerts
            </label>
          </div>
          <fieldset className="form-section">
            <legend>Inbox event types</legend>
            <p className="muted" style={{ fontSize: "0.78rem", margin: "0 0 0.4rem" }}>
              Leave all unchecked to receive every type.
            </p>
            <div className="form-grid">
              {NOTIFICATION_TYPES.map(([code, label]) => (
                <label className="checkline" key={code}>
                  <input
                    type="checkbox"
                    checked={prefs.types.includes(code)}
                    onChange={() => toggleType(code)}
                  />
                  {label}
                </label>
              ))}
            </div>
          </fieldset>
          <div className="form-actions">
            <button type="submit" className="secondary" disabled={prefBusy} aria-busy={prefBusy || undefined}>
              {prefBusy ? "Saving…" : <RollingLabel>Save preferences</RollingLabel>}
            </button>
          </div>
        </form>
      </div>

      <TableToolbar
        title="notifications"
        controls={controls}
        onRefresh={() => { notifications.reload(); unread.reload(); }}
      />
      <DataTable
        columns={[
          { key: "title", label: "Alert", render: (row) => row.is_read ? row.title : <strong>{row.title}</strong> },
          { key: "notification_type", label: "Type", render: (row) => row.notification_type },
          { key: "created_at", label: "Received", render: (row) => formatDateTime(row.created_at) },
          {
            key: "status",
            label: "Status",
            render: (row) => <span className={`tag ${row.is_read ? "good" : "info"}`}>{row.is_read ? "Read" : "Unread"}</span>,
          },
          {
            key: "actions",
            label: "Actions",
            render: (row) => (
              <div className="row-actions">
                <button
                  type="button"
                  className="ghost small"
                  aria-label={`Open ${row.title}`}
                  onClick={() => setSelected(row)}
                >
                  <RollingLabel>Open</RollingLabel>
                </button>
                {!row.is_read && (
                  <button
                    type="button"
                    className="secondary small"
                    aria-label={`Mark ${row.title} as read`}
                    disabled={busy}
                    onClick={() => act(`/communications/notifications/${row.id}/mark-read/`, "Marked as read.")}
                  >
                    <RollingLabel>Mark read</RollingLabel>
                  </button>
                )}
              </div>
            ),
          },
        ]}
        rows={rows}
        loading={notifications.loading || unread.loading}
        error={loadError ? readableError(loadError, somethingWrong) : null}
        emptyTitle={controls.query ? "No matching alerts" : emptyState.title}
        emptyHint={controls.query ? searchHint : emptyState.message}
      />
      <TablePagination controls={controls} />

      {selected && (
        <Modal title={selected.title} onClose={() => setSelected(null)}>
          <p className="muted">{formatDateTime(selected.created_at)} · {selected.notification_type}</p>
          <p>{selected.body || "No further details were supplied."}</p>
          {selected.link && (
            <p><Link className="button-link secondary" to={selected.link}>Go to the related page</Link></p>
          )}
          <div className="form-actions">
            <button type="button" className="ghost" onClick={() => setSelected(null)}>
              <RollingLabel>Close</RollingLabel>
            </button>
            {!selected.is_read && (
              <button
                type="button"
                disabled={busy}
                onClick={async () => {
                  await act(`/communications/notifications/${selected.id}/mark-read/`, "Marked as read.");
                  setSelected(null);
                }}
              >
                <RollingLabel>Mark as read</RollingLabel>
              </button>
            )}
          </div>
        </Modal>
      )}
    </section>
  );
}
