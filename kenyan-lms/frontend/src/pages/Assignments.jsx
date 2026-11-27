import ManagedResourcePage from "../components/ManagedResourcePage";
import { formatDateTime } from "../utilities/format";

export default function Assignments() {
  return (
    <ManagedResourcePage
      title="Assignments"
      overline="Learning management"
      endpoint="/courses/assignments/"
      access="staff"
      columns={[
        { key: "title", label: "Assignment" },
        { key: "course", label: "Course ID" },
        { key: "due_date", label: "Due", render: (r) => formatDateTime(r.due_date) },
        { key: "max_score", label: "Max score" },
        { key: "rubric_name", label: "Rubric", render: (r) => r.rubric_name || "Direct score" },
        { key: "max_attempts", label: "Attempts", render: (r) => r.max_attempts || 1 },
        { key: "is_published", label: "Published", render: (r) => (r.is_published ? "Yes" : "No") },
      ]}
      fields={[
        { name: "title", label: "Title", required: true, full: true },
        { name: "course", label: "Course ID", required: true },
        { name: "instructions", label: "Instructions", type: "textarea", full: true },
        { name: "max_score", label: "Max score", type: "number", default: 100 },
        { name: "rubric", label: "Rubric", type: "select", optionsEndpoint: "/curriculum/rubrics/", labelKey: "name", hint: "Optional. Choose a rubric to use the criterion marking grid." },
        { name: "allow_resubmission", label: "Allow resubmission", type: "checkbox", hint: "Learners may send a new attempt up to the limit below." },
        { name: "max_attempts", label: "Maximum attempts", type: "number", default: 1 },
        { name: "is_published", label: "Published", type: "checkbox" },
      ]}
      emptyHint="Assignments belong to a course."
    />
  );
}
