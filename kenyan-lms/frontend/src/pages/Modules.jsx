import ManagedResourcePage from "../components/ManagedResourcePage";

export default function Modules() {
  return (
    <ManagedResourcePage
      title="Course modules"
      overline="Learning management"
      endpoint="/courses/modules/"
      columns={[
        { key: "title", label: "Module" },
        { key: "course", label: "Course ID" },
        { key: "sequence", label: "Order" },
        { key: "lesson_count", label: "Lessons", render: (r) => (r.lessons || []).length },
      ]}
      fields={[
        { name: "course", label: "Course ID", required: true },
        { name: "title", label: "Module title", required: true, full: true },
        { name: "description", label: "Description", type: "textarea", full: true },
        { name: "sequence", label: "Order", type: "number", default: 1 },
      ]}
      emptyHint="Modules group lessons inside a course. Create the course first."
    />
  );
}
