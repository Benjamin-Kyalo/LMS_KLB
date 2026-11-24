import ManagedResourcePage from "../components/ManagedResourcePage";

export default function Curriculum() {
  return (
    <ManagedResourcePage
      title="Curriculum frameworks"
      overline="Kenyan CBE"
      endpoint="/curriculum/frameworks/"
      columns={[
        { key: "name", label: "Framework" },
        { key: "code", label: "Code", render: (r) => <span className="mono">{r.code}</span> },
        { key: "version", label: "Version" },
        { key: "is_active", label: "Active", render: (r) => (r.is_active ? "Yes" : "No") },
      ]}
      fields={[
        { name: "name", label: "Name", required: true, full: true },
        { name: "code", label: "Code", hint: "Optional. CFW-0001 is generated if blank." },
        { name: "version", label: "Version", default: "1.0" },
        { name: "description", label: "Description", type: "textarea", full: true },
        { name: "is_active", label: "Active", type: "checkbox", default: true },
      ]}
      emptyHint="Frameworks are version-aware so curriculum changes never break old records."
    />
  );
}
