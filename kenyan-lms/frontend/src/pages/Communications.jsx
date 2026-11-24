import ManagedResourcePage from "../components/ManagedResourcePage";
import { formatDateTime } from "../utilities/format";

export default function Communications() {
  return (
    <ManagedResourcePage
      title="Announcements"
      overline="Communication"
      endpoint="/communications/announcements/"
      columns={[
        { key: "title", label: "Title" },
        { key: "author_name", label: "Author" },
        { key: "published_at", label: "Published", render: (r) => formatDateTime(r.published_at) },
        { key: "is_published", label: "Live", render: (r) => (r.is_published ? "Yes" : "No") },
      ]}
      fields={[
        { name: "title", label: "Title", required: true, full: true },
        { name: "body", label: "Message", type: "textarea", required: true, full: true },
        { name: "is_published", label: "Publish now", type: "checkbox", default: true },
        { name: "pinned", label: "Pin to top", type: "checkbox" },
      ]}
      emptyHint="Announcements reach the roles you choose."
    />
  );
}
