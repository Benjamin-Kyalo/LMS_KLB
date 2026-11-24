import ManagedResourcePage from "../components/ManagedResourcePage";
import { useAuth } from "../context/AuthContext";
import { isPlatform } from "../utilities/roles";

export default function Institutions() {
  const { user } = useAuth();
  return (
    <ManagedResourcePage
      title="Institutions"
      overline="Platform administration"
      endpoint="/institutions/"
      canCreate={isPlatform(user)}
      columns={[
        { key: "name", label: "Name" },
        { key: "code", label: "Code", render: (r) => <span className="mono">{r.code}</span> },
        { key: "institution_type_name", label: "Type" },
        { key: "county", label: "County" },
        { key: "user_count", label: "Users" },
      ]}
      fields={[
        { name: "name", label: "Institution name", required: true, full: true },
        { name: "code", label: "Code", hint: "Optional. Generated from the school name when left blank." },
        { name: "institution_type", label: "Type ID", required: true },
        { name: "county", label: "County" },
        { name: "town", label: "Town" },
        { name: "email", label: "Email", type: "email" },
        { name: "phone", label: "Phone" },
      ]}
      emptyHint="Platform administrators register schools here."
    />
  );
}
