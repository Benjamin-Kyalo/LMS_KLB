import ManagedResourcePage from "../components/ManagedResourcePage";

export default function Chapters() {
  return (
    <ManagedResourcePage
      title="Textbook chapters"
      overline="Digital publishing"
      endpoint="/content/chapters/"
      columns={[
        { key: "chapter_number", label: "No." },
        { key: "title", label: "Chapter" },
        { key: "textbook", label: "Textbook ID" },
        { key: "is_downloadable", label: "Downloadable", render: (r) => (r.is_downloadable ? "Yes" : "No") },
      ]}
      fields={[
        { name: "textbook", label: "Textbook ID", required: true },
        { name: "chapter_number", label: "Chapter number", type: "number", default: 1 },
        { name: "title", label: "Chapter title", required: true, full: true },
        { name: "content", label: "Content", type: "textarea", full: true },
        { name: "sequence", label: "Order", type: "number", default: 1 },
        { name: "is_downloadable", label: "Downloadable", type: "checkbox", default: true },
      ]}
      emptyHint="Chapters belong to a textbook in the catalogue."
    />
  );
}
