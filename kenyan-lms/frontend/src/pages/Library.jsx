import PublicHeader from "../components/PublicHeader";
import PublicFooter from "../components/PublicFooter";
import PublicBookShelf from "../components/PublicBookShelf";
import ResourceCatalogue from "../components/ResourceCatalogue";
import { useSiteContent } from "../context/SiteContentContext";
import { useSectionStyle } from "../styles/sectionStyles";

export default function Library() {
  const { content } = useSiteContent();
  const sectionStyle = useSectionStyle("library");

  return (
    <div className="public-page">
      <PublicHeader ariaLabel="Library navigation" />
      <main className="public-main view-enter section-styled" style={sectionStyle}>
        <div className="library-intro page-head">
          <div>
            <div className="overline">{content.library.overline}</div>
            <h1>{content.library.title}</h1>
            <p className="muted">{content.library.description}</p>
          </div>
        </div>

        <PublicBookShelf
          overline={content.library.booksOverline}
          title={content.library.booksTitle}
          description={content.library.booksDescription}
        />

        <ResourceCatalogue
          className="library-catalogue"
          endpoint="/content/public/resources/"
          overline={content.library.resourcesOverline}
          title={content.library.resourcesTitle}
          description={content.library.resourcesDescription}
          headingLevel="h2"
        />
      </main>
      <PublicFooter />
    </div>
  );
}
