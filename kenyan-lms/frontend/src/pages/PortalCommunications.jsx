import PortalList from "../components/PortalList";
import { formatDateTime } from "../utilities/format";

export default function PortalCommunications() {
  return (
    <PortalList
      title="School messages"
      overline="Communication"
      endpoint="/communications/announcements/"
      columns={[
        { key: "title", label: "Title" },
        { key: "author_name", label: "Author" },
        { key: "published_at", label: "Published", render: (r) => formatDateTime(r.published_at) },
      ]}
      emptyHint="Published announcements for your role will appear here."
    />
  );
}
