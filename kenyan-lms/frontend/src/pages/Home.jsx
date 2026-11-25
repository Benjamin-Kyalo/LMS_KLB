import { useState } from "react";
import { Link } from "react-router-dom";
import { BarChart3, BookOpen, GraduationCap, Library, Users } from "lucide-react";
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

function Icon({ name, mapping }) {
  const Component = mapping[name] || BookOpen;
  return <Component size={20} strokeWidth={1.8} />;
}

export default function Home() {
  const { content } = useSiteContent();
  const roles = content.roles?.cards || [];
  const [selectedRoleKey, setSelectedRoleKey] = useState(roles[0]?.key || "");
  const selectedRole = roles.find((item) => item.key === selectedRoleKey) || roles[0];
  const hero = content.hero;
  const workspaces = content.workspaces;
  const insights = content.insights;
  const roleCopy = content.roles;
  const heroStyle = sectionStyleVars(content.styles, "hero");
  const workspaceHeadingStyle = sectionStyleVars(content.styles, "workspaces");
  const insightStyle = sectionStyleVars(content.styles, "insights");
  const roleStyle = sectionStyleVars(content.styles, "roles");

  return (
    <div className="public-home">
      <PublicHeader />

      <main>
        <section className="public-hero view-enter section-styled" style={heroStyle}>
          <div className="public-hero-copy">
            <div className="overline">{hero.overline}</div>
            <ParticleHeadline text={hero.title} />
            <p>{hero.description}</p>
            <div className="public-hero-actions">
              <Link to={hero.primaryHref} className="button-link light">
                <RollingLabel>{hero.primaryLabel}</RollingLabel>
              </Link>
              <Link to={hero.secondaryHref} className="button-link light outline">
                <RollingLabel>{hero.secondaryLabel}</RollingLabel>
              </Link>
            </div>
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
                <Link to={selectedRole.to} className="button-link">
                  <RollingLabel>{selectedRole.action}</RollingLabel>
                </Link>
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
      </main>

      <PublicFooter />
    </div>
  );
}
