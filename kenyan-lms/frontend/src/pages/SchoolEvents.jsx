import ManagedResourcePage from "../components/ManagedResourcePage";
import { formatDateTime } from "../utilities/format";

const EVENT_TYPES = [
  { value: "EXAM", label: "Examination" }, { value: "HOLIDAY", label: "Holiday" },
  { value: "MEETING", label: "Meeting" }, { value: "SPORTS", label: "Sports" },
  { value: "OTHER", label: "Other" },
];

export default function SchoolEvents() {
  return (
    <ManagedResourcePage
      title="School events"
      overline="Calendar"
      endpoint="/academics/events/"
      columns={[
        { key: "title", label: "Event" },
        { key: "event_type", label: "Type" },
        { key: "start_datetime", label: "Starts", render: (r) => formatDateTime(r.start_datetime) },
        { key: "end_datetime", label: "Ends", render: (r) => formatDateTime(r.end_datetime) },
        { key: "is_published", label: "Published", render: (r) => (r.is_published ? "Yes" : "No") },
      ]}
      fields={[
        { name: "title", label: "Title", required: true, full: true },
        { name: "event_type", label: "Type", type: "select", options: EVENT_TYPES, default: "OTHER" },
        { name: "start_datetime", label: "Starts", type: "datetime-local", required: true },
        { name: "end_datetime", label: "Ends", type: "datetime-local" },
        { name: "description", label: "Description", type: "textarea", full: true },
        { name: "institution", label: "School ID", type: "select", optionsEndpoint: "/institutions/", labelKey: "name", required: true },
        { name: "is_published", label: "Published", type: "checkbox" },
      ]}
      emptyHint="Record exams, holidays, meetings and sports days."
    />
  );
}
