import ManagedResourcePage from "../components/ManagedResourcePage";

export default function Classes() {
  return (
    <ManagedResourcePage
      title="Classes"
      overline="Academic structure"
      endpoint="/institutions/classes/"
      columns={[
        { key: "name", label: "Class" },
        { key: "level", label: "Level" },
        { key: "stream", label: "Stream" },
        { key: "academic_year_name", label: "Academic year" },
        { key: "capacity", label: "Capacity" },
        { key: "class_teacher_name", label: "Class teacher" },
      ]}
      fields={[
        { name: "name", label: "Class name", required: true, hint: "For example Grade 7 or Form 3." },
        { name: "level", label: "Level", hint: "For example Grade 7, Form 3, Year 2." },
        { name: "stream", label: "Stream", hint: "Optional, for example East or A." },
        { name: "academic_year", label: "Academic year", type: "select", optionsEndpoint: "/institutions/academic-years/", labelKey: "name", required: true },
        { name: "institution", label: "School ID", type: "select", optionsEndpoint: "/institutions/", labelKey: "name", required: true },
        { name: "capacity", label: "Capacity", type: "number", default: 40 },
      ]}
      emptyHint="Add an academic year first, then create the classes for it."
    />
  );
}
