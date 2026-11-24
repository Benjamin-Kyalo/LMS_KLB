export default function SampleDataBadge({ code }) {
  const isSample = code === "DEMO01" || String(code || "").startsWith("SMP");
  if (!isSample) return null;

  return (
    <span className="sample-badge" title="Fictional records for demonstration and testing only">
      SAMPLE DATA
    </span>
  );
}
