import ManagedResourcePage from "../components/ManagedResourcePage";
import { statusTag } from "../utilities/format";

export default function Courses() {
  return (
    <ManagedResourcePage
      title="Courses"
      overline="Learning management"
      endpoint="/courses/"
      columns={[
        { key: "title", label: "Course" },
        { key: "subject_name", label: "Subject" },
        { key: "teacher_name", label: "Teacher" },
        { key: "module_count", label: "Modules" },
        { key: "status", label: "Status", render: (r) => statusTag(r.status) },
      ]}
      fields={[
        { name: "title", label: "Course title", required: true, full: true },
        { name: "code", label: "Code", hint: "Optional. CRS-SCHOOL-001 is generated if blank." },
        { name: "description", label: "Description", type: "textarea", full: true },
        { name: "status", label: "Status", type: "select", options: [
          { value: "DRAFT", label: "Draft" }, { value: "PUBLISHED", label: "Published" },
        ], default: "DRAFT" },
      ]}
      emptyHint="Create a course, then add modules and lessons from the API."
    />
  );
}
