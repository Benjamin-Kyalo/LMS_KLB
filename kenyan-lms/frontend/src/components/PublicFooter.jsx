import { useSiteContent } from "../context/SiteContentContext";
import { useSectionStyle } from "../styles/sectionStyles";

function safeHref(value) {
  const href = String(value || "");
  if (href.startsWith("/") && !href.startsWith("//")) return href;
  if (/^https:\/\//i.test(href)) return href;
  return "/";
}

export default function PublicFooter() {
  const { content } = useSiteContent();
  const footer = content.footer;
  const sectionStyle = useSectionStyle("footer");

  return (
    <footer className="public-footer section-styled" style={sectionStyle}>
      <div>
        <strong>{footer.name}</strong>
        {footer.lines.map((line) => <span key={line}>{line}</span>)}
      </div>
      <span className="public-footer-credit">
        {footer.credit.prefix}
        <a
          href={safeHref(footer.credit.linkHref)}
          target="_blank"
          rel="noreferrer"
        >
          {footer.credit.linkLabel}
        </a>
        {footer.credit.suffix}
      </span>
    </footer>
  );
}
