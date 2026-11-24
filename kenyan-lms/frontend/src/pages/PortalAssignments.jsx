import PortalList from "../components/PortalList";
import { formatDateTime } from "../utilities/format";

export default function PortalAssignments() {
  return (
    <PortalList
      title="Assignments"
      overline="Learning"
      endpoint="/courses/assignments/"
      columns={[
        { key: "title", label: "Assignment" },
        { key: "course", label: "Course ID" },
        { key: "due_date", label: "Due", render: (r) => formatDateTime(r.due_date) },
        { key: "max_score", label: "Max score" },
        { key: "is_published", label: "Published", render: (r) => (r.is_published ? "Yes" : "No") },
      ]}
      emptyHint="No assignments have been published to your account yet."
    />
  );
}
