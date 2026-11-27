import { useEffect, useId, useState } from "react";
import { Link } from "react-router-dom";
import { Menu, X } from "lucide-react";
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

function HeaderLink({ item, className = "", onNavigate }) {
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
          onClick={onNavigate}
        >
          {item?.label}
        </a>
        <span id={newTabHintId} className="sr-only">Opens in a new tab</span>
      </>
    );
  }
  return (
    <Link to={href} className={className} onClick={onNavigate}>
      {item?.label}
    </Link>
  );
}

export default function PublicHeader({
  links, ariaLabel = "Public navigation", showSignIn = true,
}) {
  const { content } = useSiteContent();
  const user = useOptionalAuth()?.user || null;
  const header = content.header;
  const items = links || header.links || [];
  const sectionStyle = useSectionStyle("header");
  const navId = useId();
  const [menuOpen, setMenuOpen] = useState(false);
  const hasNav = items.length > 0 || showSignIn;

  useEffect(() => {
    if (!menuOpen) return undefined;
    const closeOnEscape = (event) => {
      if (event.key === "Escape") setMenuOpen(false);
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [menuOpen]);

  const closeMenu = () => setMenuOpen(false);

  return (
    <header className="public-topbar view-enter section-styled" style={sectionStyle}>
      <div className="public-topbar-inner">
        <Link to="/" className="public-brand" onClick={closeMenu}>
          <span className="public-mark">{header.brand.mark}</span>
          <span>
            <strong>{header.brand.name}</strong>
            <small>{header.brand.subtitle}</small>
          </span>
        </Link>
        {hasNav && (
          <>
            <button
              type="button"
              className="public-nav-toggle"
              aria-expanded={menuOpen}
              aria-controls={navId}
              onClick={() => setMenuOpen((open) => !open)}
            >
              {menuOpen ? <X size={18} strokeWidth={2} aria-hidden="true" /> : <Menu size={18} strokeWidth={2} aria-hidden="true" />}
              <span>{menuOpen ? "Close menu" : "Menu"}</span>
            </button>
            <nav
              id={navId}
              className={`public-nav${menuOpen ? " is-open" : ""}`}
              aria-label={ariaLabel}
            >
              {items.map((item, index) => (
                <HeaderLink
                  key={`${item?.href}-${index}`}
                  item={item}
                  className="public-nav-link"
                  onNavigate={closeMenu}
                />
              ))}
              {showSignIn && (
                user ? (
                  <Link
                    to={homeFor(user)}
                    className="button-link public-nav-cta"
                    onClick={closeMenu}
                  >
                    {user.full_name || user.username} dashboard
                  </Link>
                ) : (
                  <HeaderLink
                    item={{ label: header.signInLabel, href: header.signInHref }}
                    className="button-link public-nav-cta"
                    onNavigate={closeMenu}
                  />
                )
              )}
            </nav>
          </>
        )}
      </div>
    </header>
  );
}
