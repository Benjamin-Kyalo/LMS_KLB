import ManagedResourcePage from "../components/ManagedResourcePage";

export default function Departments() {
  return (
    <ManagedResourcePage
      title="Departments"
      overline="Organisation"
      endpoint="/institutions/departments/"
      columns={[
        { key: "name", label: "Department" },
        { key: "code", label: "Code", render: (r) => <span className="mono">{r.code || "—"}</span> },
        { key: "head_of_department", label: "Head" },
        { key: "is_active", label: "Active", render: (r) => (r.is_active ? "Yes" : "No") },
      ]}
      fields={[
        { name: "name", label: "Department name", required: true, full: true },
        { name: "code", label: "Code", hint: "Optional. DEP-SCHOOL-001 is generated if blank." },
        { name: "head_of_department", label: "Head of department" },
        { name: "description", label: "Description", type: "textarea", full: true },
        { name: "institution", label: "School ID", type: "select", optionsEndpoint: "/institutions/", labelKey: "name", required: true },
        { name: "is_active", label: "Active", type: "checkbox", default: true },
      ]}
      emptyHint="Create departments such as Mathematics, Languages and Guidance."
    />
  );
}
