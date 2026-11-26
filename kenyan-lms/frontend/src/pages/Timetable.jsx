import ManagedResourcePage from "../components/ManagedResourcePage";

const DAYS = [
  { value: "MONDAY", label: "Monday" }, { value: "TUESDAY", label: "Tuesday" },
  { value: "WEDNESDAY", label: "Wednesday" }, { value: "THURSDAY", label: "Thursday" },
  { value: "FRIDAY", label: "Friday" }, { value: "SATURDAY", label: "Saturday" },
  { value: "SUNDAY", label: "Sunday" },
];

export default function Timetable() {
  return (
    <ManagedResourcePage
      title="Timetable"
      overline="School calendar"
      endpoint="/academics/timetable/"
      columns={[
        { key: "day_of_week", label: "Day", render: (r) => DAYS.find((d) => d.value === r.day_of_week)?.label || r.day_of_week },
        { key: "start_time", label: "From" },
        { key: "end_time", label: "To" },
        { key: "school_class_name", label: "Class" },
        { key: "subject_name", label: "Subject" },
        { key: "teacher_name", label: "Teacher" },
      ]}
      fields={[
        { name: "day_of_week", label: "Day", type: "select", options: DAYS, required: true },
        { name: "start_time", label: "Start time", type: "time", required: true },
        { name: "end_time", label: "End time", type: "time", required: true },
        { name: "school_class", label: "Class", type: "select", optionsEndpoint: "/institutions/classes/", labelKey: "display_name", required: true },
        { name: "term", label: "Term", type: "select", optionsEndpoint: "/institutions/terms/", labelKey: "name", required: true },
        { name: "subject", label: "Subject", type: "select", optionsEndpoint: "/institutions/subjects/", labelKey: "name", required: true },
        { name: "teacher", label: "Teacher", type: "select", optionsEndpoint: "/teachers/", labelKey: "teacher_name" },
        { name: "institution", label: "School ID", type: "select", optionsEndpoint: "/institutions/", labelKey: "name", required: true },
      ]}
      emptyHint="Add classes, terms and subjects first, then build the weekly timetable."
    />
  );
}
