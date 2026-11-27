import PublicHeader from "../components/PublicHeader";
import PublicFooter from "../components/PublicFooter";
import PublicBookShelf from "../components/PublicBookShelf";
import ResourceCatalogue from "../components/ResourceCatalogue";
import { useSiteContent } from "../context/SiteContentContext";
import { useSectionStyle } from "../styles/sectionStyles";

function ManagedList({ items = [], className = "" }) {
  return (
    <ul className={className}>
      {items.filter(Boolean).map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}
    </ul>
  );
}

export default function Library() {
  const { content } = useSiteContent();
  const sectionStyle = useSectionStyle("library");
  const libraryPage = content.publicPages?.library || {};

  return (
    <div className="public-page">
      <PublicHeader ariaLabel="Library navigation" />
      <main className="public-main view-enter section-styled" style={sectionStyle}>
        <div className="library-intro page-head">
          <div>
            <div className="overline">{content.library.overline}</div>
            <h1>{libraryPage.pageTitle}</h1>
            <p className="muted">{content.library.description}</p>
          </div>
        </div>

        <section className="library-guide panel" aria-labelledby="library-guide-title">
          <h2 id="library-guide-title">{libraryPage.title}</h2>
          <div className="public-prose">
            {(libraryPage.introduction || []).map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
          </div>
          <div className="library-guide-groups">
            <div className="library-guide-group">
              <h3>{libraryPage.categoriesTitle}</h3>
              <ManagedList items={libraryPage.categories} className="library-guide-categories" />
              <p className="library-guide-search">{libraryPage.searchPlaceholder}</p>
            </div>
            <div className="library-guide-group">
              <ManagedList items={libraryPage.filters} className="library-guide-filters" />
              <ManagedList items={libraryPage.accessLabels} className="library-guide-access" />
            </div>
          </div>
        </section>

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
