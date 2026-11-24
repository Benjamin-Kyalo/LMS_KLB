import ManagedResourcePage from "../components/ManagedResourcePage";

// Subjects are the KLB learning areas offered by the institution.
// School classes live in Classes.jsx.
export default function Subjects() {
  return (
    <ManagedResourcePage
      title="Subjects"
      overline="Academic structure"
      endpoint="/institutions/subjects/"
      columns={[
        { key: "name", label: "Subject" },
        { key: "code", label: "Code", render: (r) => <span className="mono">{r.code || "—"}</span> },
        { key: "learning_area", label: "Learning area" },
        { key: "is_active", label: "Active", render: (r) => (r.is_active ? "Yes" : "No") },
      ]}
      fields={[
        { name: "name", label: "Subject name", required: true, full: true },
        { name: "code", label: "Code", hint: "Optional. SUB-SCHOOL-001 is generated if blank." },
        { name: "learning_area", label: "Learning area" },
        { name: "institution", label: "School ID", type: "select", optionsEndpoint: "/institutions/", labelKey: "name", required: true },
        { name: "is_active", label: "Active", type: "checkbox", default: true },
      ]}
      emptyHint="Add the subjects this institution teaches."
    />
  );
}
