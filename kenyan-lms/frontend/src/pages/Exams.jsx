import ManagedResourcePage from "../components/ManagedResourcePage";
import { formatDate } from "../utilities/format";

export default function Exams() {
  return (
    <ManagedResourcePage
      title="Exams"
      overline="Assessment"
      endpoint="/assessments/exams/"
      columns={[
        { key: "title", label: "Exam" },
        { key: "subject_name", label: "Subject" },
        { key: "exam_date", label: "Date", render: (r) => formatDate(r.exam_date) },
        { key: "max_score", label: "Max score" },
      ]}
      fields={[
        { name: "title", label: "Exam title", required: true, full: true },
        { name: "exam_date", label: "Date", type: "date" },
        { name: "max_score", label: "Max score", type: "number", default: 100 },
      ]}
      emptyHint="Record exams, then enter results per learner."
    />
  );
}
