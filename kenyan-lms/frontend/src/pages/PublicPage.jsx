import { useId, useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import PublicHeader from "../components/PublicHeader";
import PublicFooter from "../components/PublicFooter";
import RollingLabel from "../components/RollingLabel";
import { useSiteContent } from "../context/SiteContentContext";
import { useSectionStyle } from "../styles/sectionStyles";
import { api } from "../services/api";

// Every route below renders the corresponding object from content.publicPages.
// The route name is the only hard-coded part; wording, links and lists all come
// from the managed site content loaded through useSiteContent().
const GENERIC_PAGES = new Set(["privacy", "terms", "acceptableUse", "accessibility"]);
const ROLE_PAGES = new Set(["teachers", "learners", "parents"]);
const PAGE_HREFS = {
  about: "/about",
  schools: "/for-schools",
  teachers: "/for-teachers",
  learners: "/for-learners",
  parents: "/for-parents",
  library: "/library",
  help: "/help",
  contact: "/contact",
  faq: "/faq",
  privacy: "/privacy",
  terms: "/terms",
  acceptableUse: "/acceptable-use",
  accessibility: "/accessibility-statement",
};

const CONTACT_FIELDS = [
  { name: "full_name", type: "text", autoComplete: "name", required: true },
  { name: "email", type: "email", autoComplete: "email", required: true },
  { name: "phone", type: "tel", autoComplete: "tel" },
  { name: "organisation", type: "text", autoComplete: "organization" },
  { name: "category", type: "select", required: true },
  { name: "subject", type: "text", required: true },
  { name: "message", type: "textarea", required: true },
];

function safeHref(value) {
  const href = String(value || "");
  if (href.startsWith("/") && !href.startsWith("//")) return href;
  if (/^https:\/\//i.test(href)) return href;
  return "/";
}

function ManagedLink({ to, children, ...rest }) {
  const href = safeHref(to);
  const newTabHintId = useId();
  if (/^https:\/\//i.test(href)) {
    return (
      <>
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          aria-describedby={newTabHintId}
          {...rest}
        >
          {children}
        </a>
        <span id={newTabHintId} className="sr-only">Opens in a new tab</span>
      </>
    );
  }
  return <Link to={href} {...rest}>{children}</Link>;
}

function Paragraphs({ items = [], className = "" }) {
  return (
    <div className={`public-prose ${className}`.trim()}>
      {items.filter(Boolean).map((text, index) => <p key={`${index}-${text.slice(0, 24)}`}>{text}</p>)}
    </div>
  );
}

function StringList({ items = [], className = "" }) {
  return (
    <ul className={className || "public-list"}>
      {items.filter(Boolean).map((text, index) => <li key={`${index}-${text.slice(0, 24)}`}>{text}</li>)}
    </ul>
  );
}

function CardList({ items = [] }) {
  if (!items.length) return null;
  return (
    <div className="public-info-cards">
      {items.map((item, index) => (
        <article className="panel public-info-card" key={`${item?.title || item?.question || index}`}>
          <h3>{item?.title || item?.question}</h3>
          {item?.copy && <p>{item.copy}</p>}
          {item?.answer && <p>{item.answer}</p>}
        </article>
      ))}
    </div>
  );
}

function ActionLink({ label, href, className = "button-link" }) {
  if (!label) return null;
  return (
    <ManagedLink to={href} className={className}>
      <RollingLabel>{label}</RollingLabel>
    </ManagedLink>
  );
}

function GenericValue({ value }) {
  if (typeof value === "string") return <p>{value}</p>;
  if (Array.isArray(value)) {
    if (value.every((item) => typeof item === "string")) return <StringList items={value} />;
    return <CardList items={value} />;
  }
  if (value && typeof value === "object") {
    if (value.title || value.question) return <CardList items={[value]} />;
    return Object.values(value).map((item, index) => <GenericValue key={index} value={item} />);
  }
  return null;
}

// Policy pages are plain prose, lists and sections supplied by the content
// pack. A "*Title" key is rendered as a heading together with the matching
// body key, so newly supplied sections appear without new component code.
// Implementer-only notes are never shown; legal-review notes are.
function isImplementerNote(pageKey, key) {
  if (/pricingNote|implementationNote|adminNote|internalNote/i.test(key)) return true;
  return pageKey === "contact" && key === "note";
}

function GenericContent({ pageKey, pageCopy }) {
  const consumed = new Set();
  const entries = Object.entries(pageCopy).filter(([key, value]) => (
    key !== "pageTitle" && key !== "title" && !isImplementerNote(pageKey, key)
    && value !== null && value !== undefined && value !== ""
  ));

  return (
    <div className="public-info-prose">
      {entries.map(([key, value]) => {
        if (consumed.has(key)) return null;
        if (/Title$/.test(key) && typeof value === "string") {
          const bodyKey = key.replace(/Title$/, "");
          const body = pageCopy[bodyKey];
          if (body !== undefined && !consumed.has(bodyKey) && !isImplementerNote(pageKey, bodyKey)) {
            consumed.add(bodyKey);
            return (
              <section className="info-section" key={key}>
                <h2>{value}</h2>
                <GenericValue value={body} />
              </section>
            );
          }
          return <h2 key={key}>{value}</h2>;
        }
        if (key === "note") {
          return (
            <aside className="public-legal-note" role="note" key={key}>
              <p>{String(value)}</p>
            </aside>
          );
        }
        return <GenericValue key={key} value={value} />;
      })}
    </div>
  );
}

function HelpPage({ page }) {
  const { content } = useSiteContent();
  const [query, setQuery] = useState("");
  const searchId = useId();
  const articles = useMemo(
    () => (page.categories || []).flatMap((category) => (
      (category.items || []).map((title) => ({ title, category: category.title }))
    )),
    [page.categories],
  );
  const needle = query.trim().toLowerCase();
  const matches = needle
    ? articles.filter((article) => article.title.toLowerCase().includes(needle))
    : articles;
  const noResults = page.noResults || content.messages?.emptyStates?.resources?.message || "";

  return (
    <div className="public-help">
      <Paragraphs items={page.introduction} />
      <div className="public-help-search">
        <label className="sr-only" htmlFor={searchId}>{page.searchPlaceholder}</label>
        <input
          id={searchId}
          type="search"
          value={query}
          placeholder={page.searchPlaceholder}
          onChange={(event) => setQuery(event.target.value)}
        />
        <p className="public-help-count" aria-live="polite">{matches.length} results</p>
      </div>
      {(page.suggestedSearches || []).length > 0 && (
        <div className="public-help-suggestions">
          {(page.suggestedSearches || []).map((suggestion) => (
            <button type="button" key={suggestion} onClick={() => setQuery(suggestion)}>
              <RollingLabel>{suggestion}</RollingLabel>
            </button>
          ))}
        </div>
      )}
      {matches.length === 0 ? (
        <p className="public-help-empty" role="status">{noResults}</p>
      ) : (
        <div className="public-help-groups">
          {(page.categories || []).map((category) => {
            const items = (category.items || []).filter((title) => (
              !needle || title.toLowerCase().includes(needle)
            ));
            if (!items.length) return null;
            return (
              <section className="info-section" key={category.title}>
                <h2>{category.title}</h2>
                <StringList items={items} />
              </section>
            );
          })}
        </div>
      )}
      {(page.supportTitle || page.supportCopy) && (
        <section className="public-help-support">
          <h2>{page.supportTitle}</h2>
          <p>{page.supportCopy}</p>
          <ActionLink label={page.actionLabel} href={page.actionHref} />
        </section>
      )}
    </div>
  );
}

function FaqPage({ page }) {
  return (
    <div className="public-faq-groups">
      <Paragraphs items={page.introduction} />
      {(page.groups || []).map((group) => (
        <section className="info-section" key={group.title}>
          <h2>{group.title}</h2>
          <div className="faq-list">
            {(group.items || []).map((item) => (
              <details className="faq-item" key={item.question}>
                <summary>{item.question}</summary>
                <p>{item.answer}</p>
              </details>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

function ContactPage({ page }) {
  const { content } = useSiteContent();
  const location = useLocation();
  const formId = useId();
  const initialCategory = useMemo(
    () => new URLSearchParams(location.search).get("category") || "",
    [location.search],
  );
  const [values, setValues] = useState({
    full_name: "", email: "", phone: "", organisation: "",
    category: initialCategory, subject: "", message: "",
  });
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [reference, setReference] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const labels = page.fields || [];
  const categories = page.categories || [];
  const fields = CONTACT_FIELDS.filter((field) => labels[CONTACT_FIELDS.indexOf(field)]);

  const onChange = (event) => {
    const { name, value } = event.target;
    setValues((current) => ({ ...current, [name]: value }));
  };

  const onSubmit = async (event) => {
    event.preventDefault();
    setSending(true);
    setError("");
    try {
      const response = await api.post("/core/public-enquiries/", values);
      setReference(response?.reference || response?.data?.reference || "");
      setSubmitted(true);
    } catch {
      // The API service already normalises failures; use the managed message
      // rather than echoing server JSON or HTML back to a visitor.
      setError(content.messages?.errors?.somethingWrong || "");
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="public-contact">
      <Paragraphs items={page.introduction} />
      {submitted && (
        <div className="public-contact-confirmation" role="status">
          <p>{page.confirmation}</p>
          {reference && <p className="public-contact-reference">{reference}</p>}
        </div>
      )}
      <form className="public-contact-form" onSubmit={onSubmit} aria-busy={sending}>
        <div className="public-contact-grid">
          {fields.map((field) => {
            const index = CONTACT_FIELDS.indexOf(field);
            const label = labels[index];
            const id = `${formId}-${field.name}`;
            return (
              <div
                className={`public-contact-field${field.name === "message" ? " full" : ""}`}
                key={field.name}
              >
                <label htmlFor={id}>{label}</label>
                {field.type === "select" ? (
                  <select
                    id={id}
                    name={field.name}
                    value={values[field.name]}
                    required={field.required}
                    onChange={onChange}
                  >
                    <option value="">{label}</option>
                    {categories.map((category) => (
                      <option value={category} key={category}>{category}</option>
                    ))}
                  </select>
                ) : field.type === "textarea" ? (
                  <textarea
                    id={id}
                    name={field.name}
                    rows={5}
                    required={field.required}
                    value={values[field.name]}
                    onChange={onChange}
                  />
                ) : (
                  <input
                    id={id}
                    name={field.name}
                    type={field.type}
                    autoComplete={field.autoComplete}
                    required={field.required}
                    value={values[field.name]}
                    onChange={onChange}
                  />
                )}
              </div>
            );
          })}
        </div>
        {error && <p className="public-contact-error" role="alert">{error}</p>}
        <div className="public-contact-actions">
          <button type="submit" disabled={sending}>
            <RollingLabel>{page.actionLabel}</RollingLabel>
          </button>
          <span className="public-contact-status" aria-live="polite">
            {sending ? "Sending enquiry…" : ""}
          </span>
        </div>
      </form>
    </div>
  );
}

function footerLabel(content, href) {
  const groups = [
    "exploreLinks", "learnLinks", "infoLinks", "supportLinks",
  ].map((key) => content.footer?.[key] || []);
  const match = groups.flat().find((item) => item?.href === href);
  return match?.label || "";
}

export default function PublicPage({ page = "about" }) {
  const { content } = useSiteContent();
  const pageCopy = content.publicPages?.[page] || {};
  const infoStyle = useSectionStyle("info");
  const heading = pageCopy.pageTitle || pageCopy.title || footerLabel(content, PAGE_HREFS[page]);
  const lead = pageCopy.title && pageCopy.title !== heading ? pageCopy.title : "";

  return (
    <div className="public-page">
      <PublicHeader />
      <main className="public-main view-enter section-styled" style={infoStyle}>
        <div className="page-head public-page-head">
          <div>
            <h1>{heading}</h1>
            {lead && <p className="public-page-lead">{lead}</p>}
          </div>
        </div>

        {page === "about" && (
          <div className="public-info-page">
            <section className="info-section">
              <Paragraphs items={pageCopy.introduction} />
              <Paragraphs items={pageCopy.brandMessage} className="public-brand-message" />
            </section>
            <section className="info-section">
              <h2>{pageCopy.approachTitle}</h2>
              <CardList items={pageCopy.approach} />
            </section>
            <section className="info-section">
              <h2>{pageCopy.commitmentTitle}</h2>
              <Paragraphs items={[pageCopy.commitment]} />
            </section>
          </div>
        )}

        {page === "schools" && (
          <div className="public-info-page">
            <section className="info-section">
              <Paragraphs items={pageCopy.introduction} />
            </section>
            <section className="info-section">
              <h2>{pageCopy.benefitsTitle}</h2>
              <CardList items={pageCopy.benefits} />
            </section>
            <div className="public-section-actions">
              <ActionLink label={pageCopy.actionLabel} href={pageCopy.actionHref} />
            </div>
          </div>
        )}

        {ROLE_PAGES.has(page) && (
          <div className="public-info-page">
            <section className="info-section">
              <Paragraphs items={pageCopy.introduction} />
            </section>
            <section className="info-section">
              <h2>{pageCopy.featuresTitle}</h2>
              <StringList items={pageCopy.features} />
            </section>
            {pageCopy.closing && <p className="public-info-closing">{pageCopy.closing}</p>}
            <div className="public-section-actions">
              <ActionLink label={pageCopy.actionLabel} href={pageCopy.actionHref} />
            </div>
          </div>
        )}

        {page === "help" && <HelpPage page={pageCopy} />}
        {page === "faq" && <FaqPage page={pageCopy} />}
        {page === "contact" && <ContactPage page={pageCopy} />}
        {GENERIC_PAGES.has(page) && <GenericContent pageKey={page} pageCopy={pageCopy} />}
      </main>
      <PublicFooter />
    </div>
  );
}
