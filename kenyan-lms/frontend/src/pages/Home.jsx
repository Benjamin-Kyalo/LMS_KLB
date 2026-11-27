import { useEffect, useId, useState } from "react";
import { Link } from "react-router-dom";
import {
  BarChart3, BookOpen, Check, ClipboardList, GraduationCap, Library, Search,
  ShieldCheck, Users, Wifi,
} from "lucide-react";
import PublicHeader from "../components/PublicHeader";
import PublicFooter from "../components/PublicFooter";
import ParticleHeadline from "../components/ParticleHeadline";
import RollingLabel from "../components/RollingLabel";
import { useSiteContent } from "../context/SiteContentContext";
import { sectionStyleVars } from "../styles/sectionStyles";

const ROLE_ICONS = {
  learners: GraduationCap,
  guardians: Users,
  teachers: BookOpen,
  content: Library,
};

const WORKSPACE_ICONS = {
  learning: GraduationCap,
  school: BarChart3,
  publishing: Library,
};

const TRUST_ICONS = {
  connected: ShieldCheck,
  roles: Users,
  modest: Wifi,
};

const ROUTINE_ICONS = {
  plan: BookOpen,
  record: ClipboardList,
  review: BarChart3,
};

const ACCESSIBILITY_ICONS = {
  keyboard: ShieldCheck,
  motion: Check,
  bandwidth: Wifi,
};

function Icon({ name, mapping }) {
  const Component = mapping[name] || BookOpen;
  return <Component size={20} strokeWidth={1.8} />;
}

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

function useReadingProgress() {
  const [progress, setProgress] = useState(0);
  useEffect(() => {
    const update = () => {
      const scrollable = document.documentElement.scrollHeight - window.innerHeight;
      setProgress(scrollable > 0 ? Math.min(1, Math.max(0, window.scrollY / scrollable)) : 0);
    };
    update();
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    return () => {
      window.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
    };
  }, []);
  return progress;
}

export default function Home() {
  const { content } = useSiteContent();
  const roles = content.roles?.cards || [];
  const [selectedRoleKey, setSelectedRoleKey] = useState(roles[0]?.key || "");
  const [announcementDismissed, setAnnouncementDismissed] = useState(false);
  const progress = useReadingProgress();
  const selectedRole = roles.find((item) => item.key === selectedRoleKey) || roles[0];
  const announcement = content.announcement || {};
  const quickLinks = content.quickLinks || {};
  const hero = content.hero;
  const trust = content.trust;
  const workspaces = content.workspaces;
  const routines = content.routines;
  const access = content.access;
  const journey = content.journey;
  const insights = content.insights;
  const accessibility = content.accessibility;
  const spotlight = content.spotlight;
  const roleCopy = content.roles;
  const support = content.support;
  const faq = content.faq;

  const announcementStyle = sectionStyleVars(content.styles, "announcement");
  const quickStyle = sectionStyleVars(content.styles, "quick-links");
  const heroStyle = sectionStyleVars(content.styles, "hero");
  const trustStyle = sectionStyleVars(content.styles, "trust");
  const workspaceHeadingStyle = sectionStyleVars(content.styles, "workspaces");
  const routineStyle = sectionStyleVars(content.styles, "routines");
  const accessStyle = sectionStyleVars(content.styles, "access");
  const journeyStyle = sectionStyleVars(content.styles, "journey");
  const insightStyle = sectionStyleVars(content.styles, "insights");
  const accessibilityStyle = sectionStyleVars(content.styles, "accessibility");
  const spotlightStyle = sectionStyleVars(content.styles, "spotlight");
  const roleStyle = sectionStyleVars(content.styles, "roles");
  const supportStyle = sectionStyleVars(content.styles, "support");
  const faqStyle = sectionStyleVars(content.styles, "faq");

  return (
    <div className="public-home">
      <a className="skip-link" href="#home-content">Skip to homepage content</a>
      <div className="reading-progress" aria-hidden="true">
        <span style={{ transform: `scaleX(${progress})` }} />
      </div>

      <PublicHeader />

      {announcement.text && !announcementDismissed && (
        <aside
          className="public-announcement section-styled"
          aria-label="Site announcement"
          style={announcementStyle}
        >
          <div className="public-announcement-inner">
            <span>{announcement.text}</span>
            {announcement.actionLabel && (
              <ManagedLink to={announcement.actionHref} className="public-announcement-link">
                <RollingLabel>{announcement.actionLabel}</RollingLabel>
              </ManagedLink>
            )}
            <button
              type="button"
              className="public-announcement-close"
              aria-label="Dismiss announcement"
              onClick={() => setAnnouncementDismissed(true)}
            >
              <RollingLabel>Dismiss</RollingLabel>
            </button>
          </div>
        </aside>
      )}

      <nav
        className="public-quick-links section-styled"
        aria-label={quickLinks.title || "On this page"}
        style={quickStyle}
      >
        <span className="public-quick-links-label">{quickLinks.title}</span>
        {(quickLinks.links || []).map((item, index) => (
          <ManagedLink
            key={`${item?.href}-${index}`}
            to={item?.href}
            className="public-quick-link"
          >
            {item?.label}
          </ManagedLink>
        ))}
      </nav>

      <main id="home-content">
        <section className="public-hero view-enter section-styled" style={heroStyle}>
          <div className="public-hero-copy">
            <div className="overline">{hero.overline}</div>
            <span className="hero-eyebrow">{hero.eyebrow}</span>
            <ParticleHeadline text={hero.title} />
            <p>{hero.description}</p>
            <div className="public-hero-actions">
              <ManagedLink to={hero.primaryHref} className="button-link light">
                <RollingLabel>{hero.primaryLabel}</RollingLabel>
              </ManagedLink>
              <ManagedLink to={hero.secondaryHref} className="button-link light outline">
                <RollingLabel>{hero.secondaryLabel}</RollingLabel>
              </ManagedLink>
            </div>
            <ul className="hero-highlights">
              {(hero.highlights || []).map((item) => (
                <li key={item}><Check size={16} strokeWidth={2.4} aria-hidden="true" /> {item}</li>
              ))}
            </ul>
          </div>
          <aside className="public-hero-panel">
            <figure>
              <img
                src={hero.imageSrc || "/images/hero-community.png"}
                alt={hero.imageAlt}
                className="hero-photo"
              />
              <figcaption>{hero.imageCaption}</figcaption>
            </figure>
          </aside>
        </section>

        <section
          className="public-trust section-styled"
          id="trust"
          aria-labelledby="trust-title"
          style={trustStyle}
        >
          <div className="overline">{trust.overline}</div>
          <h2 id="trust-title">{trust.title}</h2>
          <ul className="trust-grid">
            {(trust.items || []).map((item) => (
              <li className="trust-item" key={item.key}>
                <span className="trust-icon" aria-hidden="true">
                  <Icon name={item.key} mapping={TRUST_ICONS} />
                </span>
                <div>
                  <strong>{item.title}</strong>
                  <p>{item.copy}</p>
                </div>
              </li>
            ))}
          </ul>
        </section>

        <section
          className="public-workspaces section-styled"
          id="workspaces"
          aria-labelledby="workspaces-title"
          style={workspaceHeadingStyle}
        >
          <div className="public-section-head">
            <div>
              <div className="overline">{workspaces.overline}</div>
              <h2 id="workspaces-title">{workspaces.title}</h2>
            </div>
          </div>
          <div className="workspace-grid">
            {(workspaces.cards || []).map((item) => (
              <article
                className={`workspace-card workspace-${item.key} section-styled`}
                key={item.key}
                style={sectionStyleVars(content.styles, `workspace-${item.key}`)}
              >
                <div className="workspace-media">
                  <img src={item.image || item.imageSrc} alt={item.imageAlt} loading="lazy" />
                  <span className="workspace-index" aria-hidden="true">{item.index}</span>
                </div>
                <div className="workspace-body">
                  <span className="workspace-icon" aria-hidden="true">
                    <Icon name={item.key} mapping={WORKSPACE_ICONS} />
                  </span>
                  <div className="overline">{item.label}</div>
                  <h3>{item.title}</h3>
                  <p>{item.copy}</p>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section
          className="public-routines section-styled"
          id="routines"
          aria-labelledby="routines-title"
          style={routineStyle}
        >
          <div className="public-section-head">
            <div>
              <div className="overline">{routines.overline}</div>
              <h2 id="routines-title">{routines.title}</h2>
              <p>{routines.description}</p>
            </div>
          </div>
          <ul className="routine-grid">
            {(routines.items || []).map((item) => (
              <li className="routine-item" key={item.key}>
                <span className="routine-icon" aria-hidden="true">
                  <Icon name={item.key} mapping={ROUTINE_ICONS} />
                </span>
                <h3>{item.title}</h3>
                <p>{item.copy}</p>
              </li>
            ))}
          </ul>
        </section>

        <section
          className="public-access section-styled"
          id="access"
          aria-labelledby="access-title"
          style={accessStyle}
        >
          <div className="public-section-head">
            <div>
              <div className="overline">{access.overline}</div>
              <h2 id="access-title">{access.title}</h2>
              <p>{access.description}</p>
            </div>
          </div>
          <div className="access-table-wrap">
            <table className="access-table">
              <caption className="sr-only">{access.title} by role</caption>
              <thead>
                <tr>
                  {(access.columns || []).map((column) => (
                    <th key={column} scope="col">{column}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(access.rows || []).map((row) => {
                  const cells = [row.role, row.sees, row.actions];
                  return (
                    <tr key={row.role}>
                      {(access.columns || []).map((column, index) => (
                        index === 0 ? (
                          <th key={`${row.role}-${column}`} scope="row">{cells[index]}</th>
                        ) : (
                          <td key={`${row.role}-${column}`}>{cells[index]}</td>
                        )
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>

        <section
          className="public-journey section-styled"
          id="journey"
          aria-labelledby="journey-title"
          style={journeyStyle}
        >
          <div className="public-section-head">
            <div>
              <div className="overline">{journey.overline}</div>
              <h2 id="journey-title">{journey.title}</h2>
              <p>{journey.description}</p>
            </div>
          </div>
          <ol className="journey-grid">
            {(journey.steps || []).map((step) => (
              <li className="journey-step" key={step.index}>
                <span className="journey-number" aria-hidden="true">{step.index}</span>
                <h3>{step.title}</h3>
                <p>{step.copy}</p>
              </li>
            ))}
          </ol>
          <aside className="journey-checklist" aria-labelledby="checklist-title">
            <h3 id="checklist-title">{journey.checklistTitle}</h3>
            <ul>
              {(journey.checklist || []).map((item) => (
                <li key={item}><Check size={16} strokeWidth={2.4} aria-hidden="true" /> {item}</li>
              ))}
            </ul>
          </aside>
        </section>

        <section
          className="public-insights section-styled"
          id="insights"
          aria-labelledby="insights-title"
          style={insightStyle}
        >
          <div className="insight-copy">
            <div className="overline">{insights.overline}</div>
            <h2 id="insights-title">{insights.title}</h2>
            <p>{insights.description}</p>
            <ul className="insight-list">
              {(insights.points || []).map((item, index) => (
                <li key={item.title}>
                  <span className="insight-point-index" aria-hidden="true">0{index + 1}</span>
                  <div>
                    <strong>{item.title}</strong>
                    <p>{item.copy}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
          <figure className="insight-visual">
            <img
              src={insights.imageSrc || "/images/insight-success.jpg"}
              alt={insights.imageAlt || ""}
              className="insight-illustration"
              loading="lazy"
            />
            <span className="insight-chip">{insights.chip}</span>
            <figcaption>{insights.caption}</figcaption>
          </figure>
        </section>

        <section
          className="public-accessibility section-styled"
          id="accessibility"
          aria-labelledby="accessibility-title"
          style={accessibilityStyle}
        >
          <div className="overline">{accessibility.overline}</div>
          <h2 id="accessibility-title">{accessibility.title}</h2>
          <ul className="accessibility-grid">
            {(accessibility.items || []).map((item) => (
              <li key={item.key}>
                <span aria-hidden="true"><Icon name={item.key} mapping={ACCESSIBILITY_ICONS} /></span>
                <div>
                  <strong>{item.title}</strong>
                  <p>{item.copy}</p>
                </div>
              </li>
            ))}
          </ul>
        </section>

        <section
          className="public-spotlight section-styled"
          id="spotlight"
          aria-labelledby="spotlight-title"
          style={spotlightStyle}
        >
          <div className="spotlight-copy">
            <div className="overline">{spotlight.overline}</div>
            <h2 id="spotlight-title">{spotlight.title}</h2>
            <p>{spotlight.description}</p>
            <ManagedLink to={spotlight.actionHref} className="button-link">
              <Search size={18} strokeWidth={2} aria-hidden="true" />
              <RollingLabel>{spotlight.actionLabel}</RollingLabel>
            </ManagedLink>
          </div>
          <figure className="spotlight-visual">
            <img
              src={spotlight.imageSrc || "/images/hero-students.jpg"}
              alt={spotlight.imageAlt}
              className="spotlight-photo"
              loading="lazy"
            />
            <figcaption>{spotlight.imageCaption}</figcaption>
          </figure>
        </section>

        <section
          className="public-section section-styled"
          id="roles"
          aria-labelledby="audience-title"
          style={roleStyle}
        >
          <div className="public-section-head">
            <div>
              <div className="overline">{roleCopy.overline}</div>
              <h2 id="audience-title">{roleCopy.title}</h2>
              <p>{roleCopy.description}</p>
            </div>
          </div>
          <div className="role-selector" role="group" aria-label="Choose a role to preview">
            {roles.map((item) => {
              const selected = item.key === selectedRole?.key;
              return (
                <button
                  type="button"
                  className={`role-choice${selected ? " is-selected" : ""}`}
                  aria-pressed={selected}
                  onClick={() => setSelectedRoleKey(item.key)}
                  key={item.key}
                >
                  <span className="audience-icon" aria-hidden="true">
                    <Icon name={item.key} mapping={ROLE_ICONS} />
                  </span>
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>
          {selectedRole && (
            <div className="role-preview" aria-live="polite">
              <div className="role-preview-intro">
                <div className="overline">{roleCopy.previewLabel}, {selectedRole.label}</div>
                <h3>{selectedRole.title}</h3>
                <p>{selectedRole.copy}</p>
                <ManagedLink to={selectedRole.to} className="button-link">
                  <RollingLabel>{selectedRole.action}</RollingLabel>
                </ManagedLink>
              </div>
              <div className="role-preview-details">
                <div>
                  <h4>{roleCopy.rightsTitle}</h4>
                  <ul>
                    {(selectedRole.rights || []).map((right) => <li key={right}>{right}</li>)}
                  </ul>
                </div>
                <div>
                  <h4>{roleCopy.contentTitle}</h4>
                  <ul>
                    {(selectedRole.content || []).map((item) => <li key={item}>{item}</li>)}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </section>

        <section
          className="public-support section-styled"
          id="support"
          aria-labelledby="support-title"
          style={supportStyle}
        >
          <div className="public-support-inner">
            <div>
              <div className="overline">{support.overline}</div>
              <h2 id="support-title">{support.title}</h2>
              <p>{support.description}</p>
            </div>
            <div className="public-support-actions">
              <ManagedLink to={support.primaryHref} className="button-link light">
                <RollingLabel>{support.primaryLabel}</RollingLabel>
              </ManagedLink>
              <ManagedLink to={support.secondaryHref} className="button-link light outline">
                <RollingLabel>{support.secondaryLabel}</RollingLabel>
              </ManagedLink>
            </div>
          </div>
        </section>

        <section
          className="public-faq section-styled"
          id="faq"
          aria-labelledby="faq-title"
          style={faqStyle}
        >
          <div className="faq-grid">
            <div className="faq-intro">
              <div className="overline">{faq.overline}</div>
              <h2 id="faq-title">{faq.title}</h2>
              <p>{faq.description}</p>
            </div>
            <div className="faq-list">
              {(faq.items || []).map((item) => (
                <details className="faq-item" key={item.question}>
                  <summary>{item.question}</summary>
                  <p>{item.answer}</p>
                </details>
              ))}
            </div>
          </div>
        </section>
      </main>

      <PublicFooter />
    </div>
  );
}
