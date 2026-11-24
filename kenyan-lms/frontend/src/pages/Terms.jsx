import ManagedResourcePage from "../components/ManagedResourcePage";
import { formatDate } from "../utilities/format";

export default function Terms() {
  return (
    <ManagedResourcePage
      title="Terms"
      overline="School calendar"
      endpoint="/institutions/terms/"
      columns={[
        { key: "name", label: "Term" },
        { key: "academic_year_name", label: "Academic year" },
        { key: "sequence", label: "Order" },
        { key: "start_date", label: "Starts", render: (r) => formatDate(r.start_date) },
        { key: "end_date", label: "Ends", render: (r) => formatDate(r.end_date) },
        { key: "is_current", label: "Current", render: (r) => (r.is_current ? "Yes" : "No") },
      ]}
      fields={[
        { name: "name", label: "Term name", required: true },
        { name: "academic_year", label: "Academic year", type: "select", optionsEndpoint: "/institutions/academic-years/", labelKey: "name", required: true },
        { name: "sequence", label: "Sequence", type: "number", default: 1 },
        { name: "start_date", label: "Start date", type: "date", required: true },
        { name: "end_date", label: "End date", type: "date", required: true },
        { name: "institution", label: "School ID", type: "select", optionsEndpoint: "/institutions/", labelKey: "name", required: true },
        { name: "is_current", label: "Current term", type: "checkbox" },
      ]}
      emptyHint="Terms are configurable; add the terms your institution actually uses."
    />
  );
}
