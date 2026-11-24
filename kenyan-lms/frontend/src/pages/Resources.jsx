import ManagedResourcePage from "../components/ManagedResourcePage";

export default function Resources() {
  return (
    <ManagedResourcePage
      title="Learning resources"
      overline="Digital publishing"
      endpoint="/content/resources/"
      columns={[
        { key: "title", label: "Resource" },
        { key: "resource_type", label: "Type", render: (r) => <span className="tag info">{r.resource_type}</span> },
        { key: "chapter", label: "Chapter ID" },
        { key: "offline_available", label: "Offline", render: (r) => (r.offline_available ? "Yes" : "No") },
      ]}
      fields={[
        { name: "title", label: "Resource title", required: true, full: true },
        { name: "chapter", label: "Chapter ID (optional)" },
        { name: "textbook", label: "Textbook ID (optional)" },
        { name: "resource_type", label: "Type", type: "select", default: "PDF", options: [
          { value: "PDF", label: "PDF" }, { value: "VIDEO", label: "Video" },
          { value: "AUDIO", label: "Audio" }, { value: "IMAGE", label: "Image" },
          { value: "INTERACTIVE", label: "Interactive" }, { value: "LINK", label: "External link" },
        ] },
        { name: "external_url", label: "External URL", full: true },
        { name: "description", label: "Description", type: "textarea", full: true },
        { name: "offline_available", label: "Available offline", type: "checkbox" },
      ]}
      emptyHint="Upload files through the API; this form handles links and metadata."
    />
  );
}
