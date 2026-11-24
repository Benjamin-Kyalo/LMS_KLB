import ManagedResourcePage from "../components/ManagedResourcePage";

export default function Quizzes() {
  return (
    <ManagedResourcePage
      title="Quizzes"
      overline="Assessment"
      endpoint="/assessments/quizzes/"
      columns={[
        { key: "title", label: "Quiz" },
        { key: "question_count", label: "Questions" },
        { key: "time_limit_minutes", label: "Minutes" },
        { key: "is_published", label: "Published", render: (r) => (r.is_published ? "Yes" : "No") },
      ]}
      fields={[
        { name: "title", label: "Quiz title", required: true, full: true },
        { name: "description", label: "Description", type: "textarea", full: true },
        { name: "time_limit_minutes", label: "Time limit (minutes)", type: "number", default: 30 },
        { name: "is_published", label: "Published", type: "checkbox" },
      ]}
      emptyHint="Create a quiz, then attach questions from the question bank."
    />
  );
}
