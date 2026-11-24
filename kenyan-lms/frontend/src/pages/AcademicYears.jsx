import ManagedResourcePage from "../components/ManagedResourcePage";
import { formatDate } from "../utilities/format";

export default function AcademicYears() {
  return (
    <ManagedResourcePage
      title="Academic years"
      overline="School calendar"
      endpoint="/institutions/academic-years/"
      columns={[
        { key: "name", label: "Year" },
        { key: "start_date", label: "Starts", render: (r) => formatDate(r.start_date) },
        { key: "end_date", label: "Ends", render: (r) => formatDate(r.end_date) },
        { key: "is_current", label: "Current", render: (r) => (r.is_current ? "Yes" : "No") },
      ]}
      fields={[
        { name: "name", label: "Name", required: true, hint: "For example 2026" },
        { name: "start_date", label: "Start date", type: "date", required: true },
        { name: "end_date", label: "End date", type: "date", required: true },
        { name: "institution", label: "School ID", type: "select", optionsEndpoint: "/institutions/", labelKey: "name", required: true },
        { name: "is_current", label: "Current year", type: "checkbox" },
      ]}
      emptyHint="Create the current academic year before adding terms, classes and timetables."
    />
  );
}
