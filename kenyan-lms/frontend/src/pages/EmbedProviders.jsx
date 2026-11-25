import ManagedResourcePage from "../components/ManagedResourcePage";

export default function EmbedProviders() {
  return (
    <ManagedResourcePage
      title="Embed providers"
      overline="Digital publishing"
      endpoint="/content/embed-providers/"
      columns={[
        { key: "name", label: "Provider" },
        { key: "host", label: "Allowed host" },
        { key: "kind", label: "Type" },
        { key: "is_active", label: "Active", render: (row) => (row.is_active ? "Yes" : "No") },
      ]}
      fields={[
        { name: "name", label: "Provider name", required: true },
        { name: "host", label: "Allowed host", hint: "For example www.youtube.com. The scheme must be HTTPS.", required: true },
        { name: "kind", label: "Provider type", type: "select", default: "YOUTUBE", options: [
          { value: "YOUTUBE", label: "YouTube" },
          { value: "VIMEO", label: "Vimeo" },
        ], required: true },
        { name: "is_active", label: "Active", type: "checkbox" },
      ]}
      emptyHint="Only active providers here can be used for curated video embeds."
    />
  );
}
