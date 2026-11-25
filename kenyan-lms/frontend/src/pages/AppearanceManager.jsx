import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { SITE_CONTENT_GROUPS, SITE_STYLE_GROUPS } from "../config/publicSite";
import { isAdmin } from "../utilities/roles";
import SiteContentManager from "./SiteContentManager";
import ThemeManager from "./ThemeManager";

const TABS = [
  { id: "palette", label: "Colours", hint: "Choose the active palette or add your own." },
  { id: "photos", label: "Photos", hint: "Replace, remove or restore managed images." },
  { id: "words", label: "Words", hint: "Edit public headings, links and explanations." },
  { id: "styles", label: "Styles", hint: "Set colours, corners and spacing for one public section." },
];

const PHOTO_GROUP = SITE_CONTENT_GROUPS.find((item) => item.id === "photos");
const WORD_GROUPS = SITE_CONTENT_GROUPS.filter((item) => item.id !== "photos");

// One destination for appearance work. The older /admin/theme and
// /admin/site-content addresses open this page with the matching tab selected.
export default function AppearanceManager({ initialTab = "palette" }) {
  const { user } = useAuth();
  const admin = isAdmin(user);
  const available = admin ? TABS : [];
  const [tab, setTab] = useState(
    available.some((item) => item.id === initialTab) ? initialTab : "palette",
  );
  const active = available.find((item) => item.id === tab) || TABS[0];

  return (
    <section className="appearance-page">
      <div className="page-head">
        <div>
          <div className="overline">Appearance</div>
          <h1>Site appearance</h1>
          <p className="muted" style={{ marginTop: "0.2rem" }}>
            Colours, photographs, public wording and section styles in one place. Each change is
            saved with the site data and applies across public pages and the learner portal.
          </p>
        </div>
      </div>

      <nav className="appearance-tabs" aria-label="Appearance sections">
        {available.map((item) => (
          <button
            type="button"
            key={item.id}
            className={`appearance-tab${item.id === tab ? " is-selected" : ""}`}
            aria-pressed={item.id === tab}
            onClick={() => setTab(item.id)}
          >
            <strong>{item.label}</strong>
            <span>{item.hint}</span>
          </button>
        ))}
      </nav>

      <p className="appearance-tab-summary muted">{active.hint}</p>
      {!admin && (
        <p className="notice error" role="alert">
          Only administrators can change site appearance.
        </p>
      )}

      <div className="appearance-content panel">
        {tab === "palette" && <ThemeManager embedded />}
        {tab === "photos" && (
          <SiteContentManager embedded initialGroup="photos" visibleGroupIds={[PHOTO_GROUP.id]} />
        )}
        {tab === "words" && (
          <SiteContentManager embedded visibleGroupIds={WORD_GROUPS.map((item) => item.id)} />
        )}
        {tab === "styles" && <SiteContentManager embedded groups={SITE_STYLE_GROUPS} />}
      </div>
    </section>
  );
}
