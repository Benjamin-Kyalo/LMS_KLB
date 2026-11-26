import ManagedResourcePage from "../components/ManagedResourcePage";

const TYPES = [
  { value: "PDF", label: "PDF" }, { value: "VIDEO", label: "Video" },
  { value: "AUDIO", label: "Audio" }, { value: "IMAGE", label: "Image" },
  { value: "INTERACTIVE", label: "Interactive" }, { value: "LINK", label: "External link" },
];

export default function Resources() {
  return (
    <ManagedResourcePage
      title="Learning resources"
      overline="Digital publishing"
      endpoint="/content/resources/"
      columns={[
        { key: "title", label: "Resource" },
        { key: "thumbnail_url", label: "Thumbnail", render: (row) => row.thumbnail_url ? <img className="admin-thumb" src={row.thumbnail_url} alt="" width="64" height="36" loading="lazy" /> : "—" },
        { key: "resource_type", label: "Type", render: (row) => <span className="tag info">{row.resource_type}</span> },
        { key: "delivery", label: "Delivery" },
        { key: "access_scope", label: "Scope" },
        { key: "status", label: "Status" },
        { key: "offline_available", label: "Downloadable", render: (row) => (row.offline_available ? "Yes" : "No") },
      ]}
      fields={[
        { name: "title", label: "Resource title", required: true, full: true },
        { name: "description", label: "Description", type: "textarea", full: true },
        { name: "resource_type", label: "Type", type: "select", default: "PDF", options: TYPES, required: true },
        { name: "delivery", label: "Delivery", type: "select", default: "UPLOAD", options: [
          { value: "UPLOAD", label: "Local file upload" },
          { value: "LINK", label: "External HTTPS link" },
          { value: "EMBED", label: "Allowlisted video embed" },
        ], required: true },
        { name: "file", label: "Upload file", type: "file", accept: ".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.png,.jpg,.jpeg,.gif,.webp,.mp3,.wav,.ogg,.mp4,.webm", full: true, hint: "Uploads need a connection. Large videos need a deployment upload-limit decision.", showWhen: (form) => form.delivery === "UPLOAD" },
        { name: "thumbnail_image", label: "Card thumbnail", type: "file", accept: "image/jpeg,image/png,image/webp", full: true, hint: "Optional JPG, PNG or WebP shown on public and portal resource cards. Existing artwork is kept unless you choose a new file." },
        { name: "external_url", label: "External URL", full: true, hint: "HTTPS links only.", showWhen: (form) => form.delivery === "LINK" },
        { name: "embed_provider", label: "Embed provider", type: "select", optionsEndpoint: "/content/embed-providers/", hint: "Only active, administrator-approved providers appear here.", showWhen: (form) => form.delivery === "EMBED" },
        { name: "embed_source_url", label: "Video URL", full: true, hint: "The server validates the host and video ID and builds the embed URL.", showWhen: (form) => form.delivery === "EMBED" },
        { name: "chapter", label: "Chapter (optional)", type: "select", optionsEndpoint: "/content/chapters/", labelKey: "title" },
        { name: "textbook", label: "Textbook (optional)", type: "select", optionsEndpoint: "/content/textbooks/", labelKey: "title" },
        { name: "education_level", label: "Education level", type: "select", optionsEndpoint: "/curriculum/levels/" },
        { name: "learning_area", label: "Learning area", type: "select", optionsEndpoint: "/curriculum/learning-areas/" },
        { name: "subject", label: "School subject", type: "select", optionsEndpoint: "/institutions/subjects/" },
        { name: "school_class", label: "School class", type: "select", optionsEndpoint: "/institutions/classes/", labelKey: "display_name" },
        { name: "collection", label: "Collection", type: "select", optionsEndpoint: "/content/collections/" },
        { name: "keywords", label: "Keywords (JSON list)", type: "json", full: true, default: '["revision"]' },
        { name: "access_scope", label: "Access scope", type: "select", default: "PUBLIC", options: [
          { value: "PUBLIC", label: "Public" },
          { value: "INSTITUTION", label: "My institution" },
          { value: "CLASS", label: "Selected class" },
        ], required: true },
        { name: "status", label: "Status", type: "select", default: "DRAFT", options: [
          { value: "DRAFT", label: "Draft" }, { value: "IN_REVIEW", label: "In review" },
          { value: "APPROVED", label: "Approved" }, { value: "PUBLISHED", label: "Published" },
          { value: "ARCHIVED", label: "Archived" },
        ], required: true },
        { name: "offline_available", label: "Downloadable", type: "checkbox" },
      ]}
      emptyHint="Add a file, validated link or allowlisted video, then publish it when it is ready."
    />
  );
}
