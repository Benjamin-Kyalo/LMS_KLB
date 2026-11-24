import ManagedResourcePage from "../components/ManagedResourcePage";

export default function Lessons() {
  return (
    <ManagedResourcePage
      title="Lessons"
      overline="Learning management"
      endpoint="/courses/lessons/"
      columns={[
        { key: "title", label: "Lesson" },
        { key: "module", label: "Module ID" },
        { key: "content_type", label: "Type", render: (r) => <span className="tag info">{r.content_type}</span> },
        { key: "estimated_minutes", label: "Minutes" },
        { key: "is_downloadable", label: "Offline", render: (r) => (r.is_downloadable ? "Yes" : "No") },
      ]}
      fields={[
        { name: "module", label: "Module ID", required: true },
        { name: "title", label: "Lesson title", required: true, full: true },
        { name: "content_type", label: "Content type", type: "select", default: "TEXT", options: [
          { value: "TEXT", label: "Text" }, { value: "VIDEO", label: "Video" },
          { value: "AUDIO", label: "Audio" }, { value: "INTERACTIVE", label: "Interactive" },
        ] },
        { name: "estimated_minutes", label: "Estimated minutes", type: "number", default: 15 },
        { name: "content", label: "Lesson content", type: "textarea", full: true },
        { name: "media_url", label: "Media URL (optional)", full: true },
        { name: "sequence", label: "Order", type: "number", default: 1 },
        { name: "is_downloadable", label: "Available offline", type: "checkbox" },
      ]}
      emptyHint="Lessons belong to a module. Tick 'Available offline' to allow caching."
    />
  );
}
