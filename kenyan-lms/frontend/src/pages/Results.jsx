import ManagedResourcePage from "../components/ManagedResourcePage";

export default function Results() {
  return (
    <ManagedResourcePage
      title="Exam results"
      overline="Assessment"
      endpoint="/assessments/results/"
      columns={[
        { key: "learner_name", label: "Learner" },
        { key: "admission_number", label: "Admission no.", render: (r) => <span className="mono">{r.admission_number}</span> },
        { key: "exam_title", label: "Exam" },
        { key: "score", label: "Score" },
        { key: "grade", label: "Grade" },
        { key: "position", label: "Position" },
      ]}
      fields={[
        { name: "exam", label: "Exam", type: "select", optionsEndpoint: "/assessments/exams/", labelKey: "title", required: true },
        { name: "learner", label: "Learner", type: "select", optionsEndpoint: "/learners/", labelKey: "learner_name", required: true },
        { name: "score", label: "Score", type: "number", required: true },
        { name: "grade", label: "Grade" },
        { name: "position", label: "Position", type: "number" },
        { name: "remarks", label: "Remarks", type: "textarea", full: true },
        { name: "institution", label: "School ID", type: "select", optionsEndpoint: "/institutions/", labelKey: "name", required: true },
      ]}
      emptyHint="Create an exam, then record each learner's score here."
    />
  );
}
