import ManagedResourcePage from "../components/ManagedResourcePage";
import { formatDate, statusTag } from "../utilities/format";

export default function Attendance() {
  return (
    <ManagedResourcePage
      title="Attendance"
      overline="Daily records"
      endpoint="/attendance/"
      columns={[
        { key: "learner_name", label: "Learner" },
        { key: "admission_number", label: "Admission no.", render: (r) => <span className="mono">{r.admission_number}</span> },
        { key: "date", label: "Date", render: (r) => formatDate(r.date) },
        { key: "status", label: "Status", render: (r) => statusTag(r.status) },
      ]}
      fields={[
        {
          name: "learner",
          label: "Learner",
          type: "select",
          required: true,
          optionsEndpoint: "/reports/my-learners/",
          labelKey: "learner_name",
          valueKey: "id",
          hint: "Choose from learners linked to your institution.",
        },
        { name: "date", label: "Date", type: "date", required: true, default: () => {
          const now = new Date();
          return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
        } },
        { name: "status", label: "Status", type: "select", options: [
          { value: "PRESENT", label: "Present" }, { value: "ABSENT", label: "Absent" },
          { value: "LATE", label: "Late" }, { value: "EXCUSED", label: "Excused" },
        ], default: "PRESENT" },
        { name: "notes", label: "Notes", type: "textarea", full: true },
      ]}
      emptyHint="One record per learner per day."
    />
  );
}
