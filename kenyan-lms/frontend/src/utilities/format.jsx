export function formatDate(value) {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString("en-KE", { day: "numeric", month: "short", year: "numeric" });
}

export function formatDateTime(value) {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString("en-KE", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

export function statusTag(status) {
  const good = new Set(["ACTIVE", "PRESENT", "COMPLETED", "PUBLISHED", "GRADED", "APPROVED", "ACHIEVING", "EXTENDING"]);
  const warn = new Set(["LATE", "IN_PROGRESS", "DRAFT", "SUBMITTED", "DEVELOPING", "IN_REVIEW", "PENDING"]);
  const cls = good.has(status) ? "good" : warn.has(status) ? "warn" : "bad";
  return <span className={`tag ${cls}`}>{String(status || "—").replace(/_/g, " ")}</span>;
}
