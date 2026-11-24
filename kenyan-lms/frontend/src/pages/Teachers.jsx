import ManagedResourcePage from "../components/ManagedResourcePage";

export default function Teachers() {
  return (
    <ManagedResourcePage
      title="Teachers"
      overline="Staff"
      endpoint="/teachers/"
      columns={[
        { key: "teacher_name", label: "Name" },
        { key: "email", label: "Email" },
        { key: "staff_number", label: "Staff no.", render: (r) => <span className="mono">{r.staff_number || "—"}</span> },
        { key: "employment_type", label: "Employment" },
        { key: "subject_names", label: "Subjects", render: (r) => (r.subject_names || []).join(", ") || "—" },
      ]}
      fields={[
        { name: "username", label: "Username", required: true },
        { name: "first_name", label: "First name", required: true },
        { name: "last_name", label: "Last name", required: true },
        { name: "email", label: "Email", type: "email" },
        { name: "staff_number", label: "Staff number", hint: "Leave blank to generate TCH-SCHOOL-001." },
        { name: "phone", label: "Phone" },
      ]}
      emptyHint="Create teacher accounts. No password is generated; issue a password reset after saving."
    />
  );
}
