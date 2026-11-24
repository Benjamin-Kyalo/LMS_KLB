import { useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useOnlineStatus } from "../hooks/useOnlineStatus";
import SyncStatus from "../components/SyncStatus";
import SyncQueuePanel from "../components/SyncQueuePanel";
import SampleDataBadge from "../components/SampleDataBadge";
import {
  ROLES, canUseAdmin, canWriteContent, canWriteTeaching,
  isAdmin, isPlatform, isTeacher,
} from "../utilities/roles";

function NavItem({ to, children, onNavigate }) {
  return (
    <NavLink
      to={to}
      end={to === "/admin"}
      onClick={onNavigate}
      className={({ isActive }) => `admin-nav-link${isActive ? " active" : ""}`}
    >
      {children}
    </NavLink>
  );
}

export default function DashboardLayout() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const online = useOnlineStatus();
  const [menuOpen, setMenuOpen] = useState(false);
  const closeMenu = () => setMenuOpen(false);

  async function handleLogout() {
    await signOut();
    navigate("/login");
  }

  const admin = isAdmin(user);
  const teaching = canWriteTeaching(user);
  const content = canWriteContent(user);

  return (
    <div className="app-shell">
      <aside className={`app-sidebar${menuOpen ? " is-open" : ""}`}>
        <div className="admin-brand" style={{ padding: "0 0.9rem 1rem" }}>
          <img
            src={user?.institution_logo || "/mark.svg"}
            alt=""
            className="school-logo"
            onError={(event) => { event.currentTarget.src = "/mark.svg"; }}
          />
          <div>
            <div className="display" style={{ fontSize: "1.2rem", color: "var(--forest)", fontWeight: 700 }}>KLB Learning</div>
            <div className="muted" style={{ fontSize: "0.75rem" }}>{user?.institution_name || "Kenya · LMS + SIS + Publishing"}</div>
            <SampleDataBadge code={user?.institution_code} />
          </div>
        </div>

        <div className="overline" style={{ padding: "0 0.9rem" }}>Overview</div>
        <NavItem to="/admin" onNavigate={closeMenu}>Dashboard</NavItem>

        {admin && (
          <>
            <div className="overline" style={{ padding: "0.8rem 0.9rem 0.2rem" }}>Administration</div>
            <NavItem to="/admin/school" onNavigate={closeMenu}>School profile</NavItem>
            <NavItem to="/admin/departments" onNavigate={closeMenu}>Departments</NavItem>
            <NavItem to="/admin/academic-years" onNavigate={closeMenu}>Academic years</NavItem>
            <NavItem to="/admin/terms" onNavigate={closeMenu}>Terms</NavItem>
            <NavItem to="/admin/classes" onNavigate={closeMenu}>Classes</NavItem>
            <NavItem to="/admin/subjects" onNavigate={closeMenu}>Subjects</NavItem>
            <NavItem to="/admin/users" onNavigate={closeMenu}>Users</NavItem>
            <NavItem to="/admin/roles" onNavigate={closeMenu}>Roles</NavItem>
            <NavItem to="/admin/invitations" onNavigate={closeMenu}>Admin invitations</NavItem>
            {isPlatform(user) && <NavItem to="/admin/institutions" onNavigate={closeMenu}>Institutions</NavItem>}
          </>
        )}

        <div className="overline" style={{ padding: "0.8rem 0.9rem 0.2rem" }}>Teaching &amp; assessment</div>
        <NavItem to="/admin/courses" onNavigate={closeMenu}>Courses</NavItem>
        <NavItem to="/admin/modules" onNavigate={closeMenu}>Modules</NavItem>
        <NavItem to="/admin/lessons" onNavigate={closeMenu}>Lessons</NavItem>
        <NavItem to="/admin/assignments" onNavigate={closeMenu}>Assignments</NavItem>
        <NavItem to="/admin/submissions" onNavigate={closeMenu}>Submissions</NavItem>
        <NavItem to="/admin/quizzes" onNavigate={closeMenu}>Quizzes</NavItem>
        <NavItem to="/admin/questions" onNavigate={closeMenu}>Question bank</NavItem>
        <NavItem to="/admin/exams" onNavigate={closeMenu}>Exams</NavItem>
        <NavItem to="/admin/results" onNavigate={closeMenu}>Exam results</NavItem>
        <NavItem to="/admin/timetable" onNavigate={closeMenu}>Timetable</NavItem>
        <NavItem to="/admin/attendance" onNavigate={closeMenu}>Attendance</NavItem>
        {teaching && <NavItem to="/admin/curriculum" onNavigate={closeMenu}>Curriculum</NavItem>}

        <div className="overline" style={{ padding: "0.8rem 0.9rem 0.2rem" }}>Publishing</div>
        <NavItem to="/admin/textbooks" onNavigate={closeMenu}>Textbooks</NavItem>
        {content && <NavItem to="/admin/chapters" onNavigate={closeMenu}>Chapters</NavItem>}
        {content && <NavItem to="/admin/resources" onNavigate={closeMenu}>Resources</NavItem>}
        {canUseAdmin(user) && <NavItem to="/admin/approval" onNavigate={closeMenu}>Approval review</NavItem>}

        <div className="overline" style={{ padding: "0.8rem 0.9rem 0.2rem" }}>School records</div>
        {canUseAdmin(user) && <NavItem to="/admin/fees" onNavigate={closeMenu}>Fees &amp; payments</NavItem>}
        {admin && <NavItem to="/admin/kemis" onNavigate={closeMenu}>KEMIS exports</NavItem>}
        {(admin || isTeacher(user)) && <NavItem to="/admin/learners" onNavigate={closeMenu}>Learners</NavItem>}
        {admin && <NavItem to="/admin/teachers" onNavigate={closeMenu}>Teachers</NavItem>}
        {admin && <NavItem to="/admin/guardians" onNavigate={closeMenu}>Guardians</NavItem>}
        <NavItem to="/admin/events" onNavigate={closeMenu}>School events</NavItem>

        <div className="overline" style={{ padding: "0.8rem 0.9rem 0.2rem" }}>Reports &amp; account</div>
        {canUseAdmin(user) && <NavItem to="/admin/communications" onNavigate={closeMenu}>Messages</NavItem>}
        {canUseAdmin(user) && <NavItem to="/admin/reports" onNavigate={closeMenu}>Reports</NavItem>}
        {canUseAdmin(user) && <NavItem to="/admin/analytics" onNavigate={closeMenu}>Analytics</NavItem>}
        {canUseAdmin(user) && <NavItem to="/admin/tutor" onNavigate={closeMenu}>Curriculum tutor</NavItem>}
        {canUseAdmin(user) && <NavItem to="/admin/sync" onNavigate={closeMenu}>Offline queue</NavItem>}
        <NavItem to="/admin/profile" onNavigate={closeMenu}>Profile</NavItem>

        <div style={{ marginTop: "1.5rem", padding: "0 0.9rem" }}>
          <div className="muted" style={{ fontSize: "0.8rem" }}>{user?.full_name || user?.username}</div>
          <div className="tag" style={{ marginTop: "0.3rem" }}>{ROLES[user?.role] || user?.role}</div>
          <button className="ghost small" style={{ marginTop: "0.7rem" }} onClick={handleLogout}>Sign out</button>
        </div>
      </aside>

      <main className="app-main">
        <button className="secondary mobile-nav-toggle" onClick={() => setMenuOpen(!menuOpen)}>
          {menuOpen ? "Hide menu" : "Show menu"}
        </button>
        {!online && (
          <div className="notice warn offline-banner" style={{ marginBottom: "1rem" }}>
            You are offline. Cached pages still work — any changes you make are queued and sent automatically when you reconnect.
          </div>
        )}
        <SyncStatus />
        {location.pathname !== "/admin/sync" && <SyncQueuePanel className="layout-sync-panel" />}
        <Outlet />
      </main>
    </div>
  );
}
