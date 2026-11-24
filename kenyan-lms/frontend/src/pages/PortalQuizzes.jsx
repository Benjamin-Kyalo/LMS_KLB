import PortalList from "../components/PortalList";

export default function PortalQuizzes() {
  return (
    <PortalList
      title="Quizzes"
      overline="Assessment"
      endpoint="/assessments/quizzes/"
      columns={[
        { key: "title", label: "Quiz" },
        { key: "question_count", label: "Questions" },
        { key: "time_limit_minutes", label: "Minutes" },
        { key: "is_published", label: "Published", render: (r) => (r.is_published ? "Yes" : "No") },
      ]}
      emptyHint="No quizzes have been published yet."
    />
  );
}
