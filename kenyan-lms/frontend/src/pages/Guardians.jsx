import ManagedResourcePage from "../components/ManagedResourcePage";

export default function Guardians() {
  return (
    <ManagedResourcePage
      title="Guardians"
      overline="Parents & guardians"
      endpoint="/guardians/"
      columns={[
        { key: "guardian_name", label: "Name" },
        { key: "email", label: "Email" },
        { key: "phone", label: "Phone" },
        { key: "relationship_to_learner", label: "Relationship" },
      ]}
      fields={[
        { name: "username", label: "Username", required: true },
        { name: "first_name", label: "First name", required: true },
        { name: "last_name", label: "Last name", required: true },
        { name: "email", label: "Email", type: "email" },
        { name: "phone", label: "Phone" },
        { name: "relationship_to_learner", label: "Relationship" },
      ]}
      emptyHint="Guardians get read-only access to their linked learners."
    />
  );
}
