import { useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useOnlineStatus } from "../hooks/useOnlineStatus";
import SyncStatus from "../components/SyncStatus";
import SyncQueuePanel from "../components/SyncQueuePanel";
import SampleDataBadge from "../components/SampleDataBadge";
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
  const navigate = useNavigate();
  const location = useLocation();
  const online = useOnlineStatus();
  const [menuOpen, setMenuOpen] = useState(false);

  async function handleLogout() {
    await signOut();
    navigate("/login");
  }

  const closeMenu = () => setMenuOpen(false);
  const roleLabel = isGuardian(user) ? "Parent / Guardian" : isLearner(user) ? "Learner" : ROLES[user?.role] || user?.role;

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
            <div className="overline" style={{ marginBottom: 0 }}>KLB Learning</div>
            <strong>{user?.institution_name || "Your school"}</strong>
            <SampleDataBadge code={user?.institution_code} />
          </div>
        </div>

        <div className="portal-account">
          <div style={{ textAlign: "right" }}>
            <div>{user?.full_name || user?.username}</div>
            <div className="muted" style={{ fontSize: "0.75rem" }}>{roleLabel}</div>
          </div>
          <button className="ghost small" onClick={handleLogout}>Sign out</button>
          <button className="secondary mobile-nav-toggle" onClick={() => setMenuOpen(!menuOpen)}>
            {menuOpen ? "Hide menu" : "Menu"}
          </button>
        </div>
      </header>

      <nav className={`portal-nav${menuOpen ? " is-open" : ""}`} aria-label="Learner portal">
        <PortalNav to="/portal" onNavigate={closeMenu}>Home</PortalNav>
        <PortalNav to="/portal/courses" onNavigate={closeMenu}>My courses</PortalNav>
        <PortalNav to="/portal/textbooks" onNavigate={closeMenu}>Textbook library</PortalNav>
        <PortalNav to="/portal/resources" onNavigate={closeMenu}>Resources</PortalNav>
        {isLearner(user) && <PortalNav to="/portal/assignments" onNavigate={closeMenu}>Assignments</PortalNav>}
        {isLearner(user) && <PortalNav to="/portal/quizzes" onNavigate={closeMenu}>Quizzes</PortalNav>}
        <PortalNav to="/portal/reports" onNavigate={closeMenu}>Progress report</PortalNav>
        {isLearner(user) && <PortalNav to="/portal/remediation" onNavigate={closeMenu}>My support tasks</PortalNav>}
        <PortalNav to="/portal/fees" onNavigate={closeMenu}>Fees</PortalNav>
        <PortalNav to="/portal/tutor" onNavigate={closeMenu}>Ask the tutor</PortalNav>
        <PortalNav to="/portal/communications" onNavigate={closeMenu}>Messages</PortalNav>
        <PortalNav to="/portal/sync" onNavigate={closeMenu}>Offline queue</PortalNav>
        <PortalNav to="/portal/profile" onNavigate={closeMenu}>My profile</PortalNav>
      </nav>

      <main className="portal-main">
        {!online && (
          <div className="notice warn offline-banner" style={{ marginBottom: "1rem" }}>
            You are offline. Cached pages still open; new changes will sync when you reconnect.
          </div>
        )}
        <SyncStatus />
        {location.pathname !== "/portal/sync" && <SyncQueuePanel className="layout-sync-panel" />}
        <Outlet />
      </main>
    </div>
  );
}
