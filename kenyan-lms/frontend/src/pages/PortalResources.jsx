import PortalList from "../components/PortalList";

export default function PortalResources() {
  return (
    <PortalList
      title="Learning resources"
      overline="Digital publishing"
      endpoint="/content/resources/"
      columns={[
        { key: "title", label: "Resource" },
        { key: "resource_type", label: "Type" },
        { key: "offline_available", label: "Offline", render: (r) => (r.offline_available ? "Yes" : "No") },
      ]}
      emptyHint="No learning resources have been shared with your institution yet."
    />
  );
}
