import ManagedResourcePage from "../components/ManagedResourcePage";
import { formatDateTime } from "../utilities/format";

export default function Assignments() {
  return (
    <ManagedResourcePage
      title="Assignments"
      overline="Learning management"
      endpoint="/courses/assignments/"
      columns={[
        { key: "title", label: "Assignment" },
        { key: "course", label: "Course ID" },
        { key: "due_date", label: "Due", render: (r) => formatDateTime(r.due_date) },
        { key: "max_score", label: "Max score" },
        { key: "is_published", label: "Published", render: (r) => (r.is_published ? "Yes" : "No") },
      ]}
      fields={[
        { name: "title", label: "Title", required: true, full: true },
        { name: "course", label: "Course ID", required: true },
        { name: "instructions", label: "Instructions", type: "textarea", full: true },
        { name: "max_score", label: "Max score", type: "number", default: 100 },
        { name: "is_published", label: "Published", type: "checkbox" },
      ]}
      emptyHint="Assignments belong to a course."
    />
  );
}
