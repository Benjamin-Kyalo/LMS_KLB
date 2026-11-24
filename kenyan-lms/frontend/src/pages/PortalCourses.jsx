import PortalList from "../components/PortalList";
import { statusTag } from "../utilities/format";

export default function PortalCourses() {
  return (
    <PortalList
      title="My courses"
      overline="Learning"
      endpoint="/courses/"
      columns={[
        { key: "title", label: "Course" },
        { key: "subject_name", label: "Subject" },
        { key: "teacher_name", label: "Teacher" },
        { key: "module_count", label: "Modules" },
        { key: "status", label: "Status", render: (r) => statusTag(r.status) },
      ]}
      emptyHint="Your school has not published any courses yet."
    />
  );
}
