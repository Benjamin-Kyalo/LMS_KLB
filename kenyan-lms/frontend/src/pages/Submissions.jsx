import ManagedResourcePage from "../components/ManagedResourcePage";
import { formatDateTime } from "../utilities/format";

const STATUSES = [
  { value: "DRAFT", label: "Draft" }, { value: "SUBMITTED", label: "Submitted" },
  { value: "GRADED", label: "Graded" }, { value: "RETURNED", label: "Returned" },
];

export default function Submissions() {
  return (
    <ManagedResourcePage
      title="Submissions"
      overline="Learning management"
      endpoint="/courses/submissions/"
      columns={[
        { key: "learner_name", label: "Learner" },
        { key: "assignment_title", label: "Assignment" },
        { key: "submitted_at", label: "Submitted", render: (r) => formatDateTime(r.submitted_at) },
        { key: "status", label: "Status" },
        { key: "score", label: "Score" },
      ]}
      fields={[
        { name: "assignment", label: "Assignment", type: "select", optionsEndpoint: "/courses/assignments/", labelKey: "title", required: true },
        { name: "learner", label: "Learner", type: "select", optionsEndpoint: "/learners/", labelKey: "learner_name", required: true },
        { name: "text_answer", label: "Answer", type: "textarea", full: true },
        { name: "status", label: "Status", type: "select", options: STATUSES, default: "SUBMITTED" },
        { name: "score", label: "Score", type: "number" },
        { name: "feedback", label: "Feedback", type: "textarea", full: true },
        { name: "institution", label: "School ID", type: "select", optionsEndpoint: "/institutions/", labelKey: "name", required: true },
      ]}
      emptyHint="Learner submissions appear here once assignments are published."
    />
  );
}
