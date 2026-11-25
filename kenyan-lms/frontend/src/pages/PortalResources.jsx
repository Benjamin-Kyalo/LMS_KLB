import ResourceCatalogue from "../components/ResourceCatalogue";

export default function PortalResources() {
  return (
    <ResourceCatalogue
      endpoint="/content/portal/resources/"
      overline="Digital publishing"
      title="Learning resources"
      description="Published resources plus material shared with your school, class or subjects."
    />
  );
}
