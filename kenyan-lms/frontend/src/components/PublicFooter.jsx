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

function FooterLink({ item, className = "" }) {
  const href = safeHref(item?.href);
  const newTabHintId = useId();
  if (/^https:\/\//i.test(href)) {
    return (
      <>
        <a
          href={href}
          className={className}
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
  return <Link to={href} className={className}>{item?.label}</Link>;
}

function FooterColumn({ title, links = [] }) {
  if (!title) return null;
  return (
    <div className="public-footer-column">
      <h2>{title}</h2>
      <ul>
        {links.map((item, index) => (
          <li key={`${item?.href}-${index}`}><FooterLink item={item} /></li>
        ))}
      </ul>
    </div>
  );
}

export default function PublicFooter() {
  const { content } = useSiteContent();
  const footer = content.footer || {};
  const sectionStyle = useSectionStyle("footer");
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
            {(footer.lines || []).map((line) => <li key={line}>{line}</li>)}
          </ul>
        </div>
        <FooterColumn title={footer.exploreTitle} links={footer.exploreLinks} />
        <FooterColumn title={footer.learnTitle} links={footer.learnLinks} />
        <FooterColumn title={footer.infoTitle} links={footer.infoLinks} />
        <FooterColumn title={footer.supportTitle} links={footer.supportLinks} />
      </div>
      <div className="public-footer-bottom">
        <div className="public-footer-notes">
          {creditText && (
            <span className="public-footer-credit">
              {credit.prefix}
              {credit.linkLabel ? (
                <FooterLink
                  item={{ label: credit.linkLabel, href: credit.linkHref }}
                  className="public-footer-credit-link"
                />
              ) : null}
              {credit.suffix}
            </span>
          )}
          {footer.closingLine && <p className="public-footer-closing">{footer.closingLine}</p>}
          {footer.disclaimer && <p className="public-footer-disclaimer">{footer.disclaimer}</p>}
        </div>
        <button type="button" className="public-back-to-top" onClick={backToTop}>
          <RollingLabel>Back to top</RollingLabel>
        </button>
      </div>
    </footer>
  );
}
