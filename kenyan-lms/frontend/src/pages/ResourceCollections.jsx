import ManagedResourcePage from "../components/ManagedResourcePage";

export default function ResourceCollections() {
  return (
    <ManagedResourcePage
      title="Resource collections"
      overline="Digital publishing"
      endpoint="/content/collections/"
      columns={[
        { key: "name", label: "Collection" },
        { key: "slug", label: "Slug" },
        { key: "description", label: "Description" },
      ]}
      fields={[
        { name: "name", label: "Collection name", required: true },
        { name: "slug", label: "Slug", hint: "Lowercase letters, numbers and hyphens. Leave blank to derive from the name." },
        { name: "description", label: "Description", type: "textarea", full: true },
      ]}
      emptyHint="Group published resources into collections for easier discovery."
    />
  );
}
