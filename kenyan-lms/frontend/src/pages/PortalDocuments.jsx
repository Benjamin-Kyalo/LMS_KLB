import ResourceCatalogue from "../components/ResourceCatalogue";

export default function PortalDocuments() {
  return (
    <ResourceCatalogue
      endpoint="/content/portal/documents/"
      overline="School documents"
      title="Forms and documents"
      description="Downloadable forms and documents shared for your school or class."
    />
  );
}
