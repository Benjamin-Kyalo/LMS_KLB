import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useSiteContent } from "../context/SiteContentContext";
import RollingLabel from "../components/RollingLabel";
import { isGuardian, isLearner, ROLES } from "../utilities/roles";

function PortalNav({ to, children, onNavigate }) {
  return (
    <NavLink
      to={to}
      end={to === "/portal"}
      onClick={onNavigate}
      className={({ isActive }) => `portal-nav-link${isActive ? " active" : ""}`}
    >
      {children}
    </NavLink>
  );
}

export default function PortalLayout() {
  const { user, signOut } = useAuth();
  const { content } = useSiteContent();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  async function handleLogout() {
    await signOut();
    navigate("/login");
  }

  const closeMenu = () => setMenuOpen(false);

  useEffect(() => {
    if (!menuOpen) return undefined;
    const closeOnEscape = (event) => {
      if (event.key === "Escape") closeMenu();
    };
    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [menuOpen]);
  const roleLabel = isGuardian(user) ? "Parent / Guardian" : isLearner(user) ? "Learner" : ROLES[user?.role] || user?.role;
  const navLabel = (key, fallback) => (
    (content.app.portalNav || []).find((item) => item.key === key)?.label || fallback
  );

  return (
    <div className="portal-shell">
      <header className="portal-header">
        <div className="portal-brand">
          <img
            src={user?.institution_logo || "/mark.svg"}
            alt=""
            className="school-logo"
            onError={(event) => { event.currentTarget.src = "/mark.svg"; }}
          />
          <div>
            <div className="overline" style={{ marginBottom: 0 }}>{content.app.portalBrand}</div>
            <strong>{user?.institution_name || "Your school"}</strong>
          </div>
        </div>

        <div className="portal-account">
          <div style={{ textAlign: "right" }}>
            <div>{user?.full_name || user?.username}</div>
            <div className="muted" style={{ fontSize: "0.75rem" }}>{roleLabel}</div>
          </div>
          <button className="ghost small" onClick={handleLogout}><RollingLabel>Sign out</RollingLabel></button>
          <button
            className="secondary mobile-nav-toggle"
            onClick={() => setMenuOpen(!menuOpen)}
            aria-expanded={menuOpen}
            aria-controls="portal-nav"
          >
            {menuOpen ? <RollingLabel>Hide menu</RollingLabel> : <RollingLabel>Menu</RollingLabel>}
          </button>
        </div>
      </header>

      <nav id="portal-nav" className={`portal-nav${menuOpen ? " is-open" : ""}`} aria-label="Learner portal">
        <PortalNav to="/portal" onNavigate={closeMenu}>{navLabel("home", "Home")}</PortalNav>
        <PortalNav to="/portal/courses" onNavigate={closeMenu}>{navLabel("courses", "My courses")}</PortalNav>
        <PortalNav to="/portal/textbooks" onNavigate={closeMenu}>{navLabel("textbooks", "Textbook library")}</PortalNav>
        <PortalNav to="/portal/resources" onNavigate={closeMenu}>{navLabel("resources", "Resources")}</PortalNav>
        <PortalNav to="/portal/documents" onNavigate={closeMenu}>{navLabel("documents", "Documents")}</PortalNav>
        {isLearner(user) && <PortalNav to="/portal/assignments" onNavigate={closeMenu}>{navLabel("assignments", "Assignments")}</PortalNav>}
        {isLearner(user) && <PortalNav to="/portal/quizzes" onNavigate={closeMenu}>{navLabel("quizzes", "Quizzes")}</PortalNav>}
        <PortalNav to="/portal/reports" onNavigate={closeMenu}>{navLabel("reports", "Progress report")}</PortalNav>
        {isLearner(user) && <PortalNav to="/portal/remediation" onNavigate={closeMenu}>{navLabel("remediation", "My support tasks")}</PortalNav>}
        <PortalNav to="/portal/fees" onNavigate={closeMenu}>{navLabel("fees", "Fees")}</PortalNav>
        <PortalNav to="/portal/tutor" onNavigate={closeMenu}>{navLabel("tutor", "Ask the tutor")}</PortalNav>
        <PortalNav to="/portal/communications" onNavigate={closeMenu}>{navLabel("communications", "Messages")}</PortalNav>
        <PortalNav to="/portal/profile" onNavigate={closeMenu}>{navLabel("profile", "My profile")}</PortalNav>
        {user?.onboarding?.is_complete === false && (
          <PortalNav to="/onboarding" onNavigate={closeMenu}>Complete setup</PortalNav>
        )}
      </nav>

      <main className="portal-main">
        <Outlet />
      </main>
    </div>
  );
}
