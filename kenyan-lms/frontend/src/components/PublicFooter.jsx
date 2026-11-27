import { useId } from "react";
import { Link } from "react-router-dom";
import RollingLabel from "./RollingLabel";
import { useSiteContent } from "../context/SiteContentContext";
import { useSectionStyle } from "../styles/sectionStyles";

function safeHref(value) {
  const href = String(value || "");
  if (href.startsWith("/") && !href.startsWith("//")) return href;
  if (/^https:\/\//i.test(href)) return href;
  return "/";
}

function FooterLink({ item }) {
  const href = safeHref(item?.href);
  const newTabHintId = useId();
  if (/^https:\/\//i.test(href)) {
    return (
      <>
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          aria-describedby={newTabHintId}
        >
          {item?.label}
        </a>
        <span id={newTabHintId} className="sr-only">Opens in a new tab</span>
      </>
    );
  }
  return <Link to={href}>{item?.label}</Link>;
}

export default function PublicFooter() {
  const { content } = useSiteContent();
  const footer = content.footer;
  const sectionStyle = useSectionStyle("footer");
  const newTabHintId = useId();
  const credit = footer.credit || {};
  const creditText = `${credit.prefix || ""}${credit.linkLabel || ""}${credit.suffix || ""}`.trim();
  const backToTop = () => {
    const reduced = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({ top: 0, behavior: reduced ? "auto" : "smooth" });
  };

  return (
    <footer className="public-footer section-styled" style={sectionStyle}>
      <div className="public-footer-inner">
        <div className="public-footer-about">
          <strong>{footer.name}</strong>
          <p>{footer.tagline}</p>
        </div>
        <div className="public-footer-column">
          <h2>{footer.contactTitle}</h2>
          <ul>
            {footer.lines.map((line) => <li key={line}>{line}</li>)}
          </ul>
        </div>
        <div className="public-footer-column">
          <h2>{footer.exploreTitle}</h2>
          <ul>
            {(footer.exploreLinks || []).map((item, index) => (
              <li key={`${item?.href}-${index}`}><FooterLink item={item} /></li>
            ))}
          </ul>
        </div>
        <div className="public-footer-column">
          <h2>{footer.learnTitle}</h2>
          <ul>
            {(footer.learnLinks || []).map((item, index) => (
              <li key={`${item?.href}-${index}`}><FooterLink item={item} /></li>
            ))}
          </ul>
        </div>
      </div>
      {creditText && (
        <div className="public-footer-bottom">
          <span className="public-footer-credit">
            {credit.prefix}
            {credit.linkLabel ? (
              <>
                <a
                  href={safeHref(credit.linkHref)}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-describedby={newTabHintId}
                >
                  {credit.linkLabel}
                </a>
                <span id={newTabHintId} className="sr-only">Opens in a new tab</span>
              </>
            ) : null}
            {credit.suffix}
          </span>
          <button type="button" className="public-back-to-top" onClick={backToTop}>
            <RollingLabel>Back to top</RollingLabel>
          </button>
        </div>
      )}
      {!creditText && (
        <div className="public-footer-bottom">
          <button type="button" className="public-back-to-top" onClick={backToTop}>
            <RollingLabel>Back to top</RollingLabel>
          </button>
        </div>
      )}
    </footer>
  );
}
