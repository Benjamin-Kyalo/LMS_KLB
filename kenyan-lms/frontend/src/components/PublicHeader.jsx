import { useId } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useSiteContent } from "../context/SiteContentContext";
import { useSectionStyle } from "../styles/sectionStyles";
import { homeFor } from "../utilities/roles";

function useOptionalAuth() {
  try {
    return useAuth();
  } catch {
    return null;
  }
}

function safeHref(value) {
  const href = String(value || "");
  if (href.startsWith("/") && !href.startsWith("//")) return href;
  if (/^https:\/\//i.test(href)) return href;
  return "/";
}

function HeaderLink({ item }) {
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

export default function PublicHeader({
  links, ariaLabel = "Public navigation", showSignIn = true,
}) {
  const { content } = useSiteContent();
  const user = useOptionalAuth()?.user || null;
  const header = content.header;
  const items = links || header.links || [];
  const sectionStyle = useSectionStyle("header");

  return (
    <header className="public-topbar view-enter section-styled" style={sectionStyle}>
      <Link to="/" className="public-brand">
        <span className="public-mark">{header.brand.mark}</span>
        <span>
          <strong>{header.brand.name}</strong>
          <small>{header.brand.subtitle}</small>
        </span>
      </Link>
      <nav aria-label={ariaLabel}>
        {items.map((item, index) => (
          <HeaderLink key={`${item?.href}-${index}`} item={item} />
        ))}
        {showSignIn && (
          user ? (
            <Link to={homeFor(user)} className="button-link">
              {user.full_name || user.username} dashboard
            </Link>
          ) : (
            <HeaderLink item={{ label: header.signInLabel, href: header.signInHref }} />
          )
        )}
      </nav>
    </header>
  );
}
