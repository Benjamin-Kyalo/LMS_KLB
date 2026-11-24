import ManagedResourcePage from "../components/ManagedResourcePage";

export default function Questions() {
  return (
    <ManagedResourcePage
      title="Question bank"
      overline="Assessment"
      endpoint="/assessments/questions/"
      columns={[
        { key: "text", label: "Question", render: (r) => (r.text || "").slice(0, 90) },
        { key: "question_type", label: "Type", render: (r) => <span className="tag info">{r.question_type}</span> },
        { key: "marks", label: "Marks" },
        { key: "correct_answer", label: "Answer" },
      ]}
      fields={[
        { name: "question_type", label: "Question type", type: "select", default: "MCQ", options: [
          { value: "MCQ", label: "Multiple choice" }, { value: "TRUE_FALSE", label: "True or false" },
          { value: "SHORT", label: "Short answer" }, { value: "ESSAY", label: "Essay" },
        ] },
        { name: "marks", label: "Marks", type: "number", default: 1 },
        { name: "text", label: "Question text", type: "textarea", required: true, full: true },
        { name: "options", label: 'MCQ options as JSON, e.g. ["70", "700", "7000"]', type: "json", default: "[]", full: true },
        { name: "correct_answer", label: "Correct answer", full: true },
        { name: "explanation", label: "Explanation", type: "textarea", full: true },
      ]}
      emptyHint="Objective questions are auto-marked; essays are graded by a teacher."
    />
  );
}
