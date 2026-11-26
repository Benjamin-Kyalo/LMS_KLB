import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  Activity,
  Building2,
  ChevronDown,
  GraduationCap,
  LayoutDashboard,
  LogOut,
  Search,
  SlidersHorizontal,
  Users,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useSiteContent } from "../context/SiteContentContext";
import {
  CAPABILITIES, canUseAdmin, canWriteContent, canWriteTeaching,
  hasCapability, isAdmin, isCustomRole, isSuperAdmin, isTeacher, roleLabel,
} from "../utilities/roles";

const GROUP_ICONS = {
  overview: LayoutDashboard,
  people: Users,
  learning: GraduationCap,
  operations: Building2,
  insights: Activity,
  system: SlidersHorizontal,
};

function isItemActive(item, pathname) {
  if (item.end) return pathname === item.to;
  return pathname === item.to || pathname.startsWith(`${item.to}/`);
}

function NavItem({ to, label, end = false, onNavigate }) {
  return (
    <NavLink
      to={to}
      end={end}
      onClick={onNavigate}
      className={({ isActive }) => `admin-nav-link${isActive ? " active" : ""}`}
    >
      {label}
    </NavLink>
  );
}

export default function DashboardLayout() {
  const { user, signOut } = useAuth();
  const { content: siteContent } = useSiteContent();
  const navigate = useNavigate();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const [query, setQuery] = useState("");

  useEffect(() => {
    setMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!menuOpen) return undefined;
    const closeOnEscape = (event) => {
      if (event.key === "Escape") setMenuOpen(false);
    };
    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [menuOpen]);

  const admin = isAdmin(user);
  const superAdmin = isSuperAdmin(user);
  const customAdmin = isCustomRole(user) && canUseAdmin(user);
  const teaching = canWriteTeaching(user);
  const content = canWriteContent(user);
  const staff = isAdmin(user) || isTeacher(user);
  // Built-in admins pass every capability check. Custom roles need the named
  // capability plus admin.access, which is already checked by customAdmin.
  const allows = (capability) => customAdmin && hasCapability(user, capability);

  const groups = [
    {
      id: "overview",
      label: "Overview",
      items: [
        { to: "/admin", label: "Dashboard", end: true },
        { to: "/admin/notifications", label: "Notifications" },
      ],
    },
    {
      id: "people",
      label: "People & access",
      items: [
        { to: "/admin/users", label: "Users", show: admin || allows(CAPABILITIES.USERS_MANAGE) },
        { to: "/admin/roles", label: "Roles", show: admin || allows(CAPABILITIES.ROLES_MANAGE) },
        { to: "/admin/invitations", label: "Admin invitations", show: admin || allows(CAPABILITIES.USERS_MANAGE) },
        { to: "/admin/teacher-approvals", label: "Teacher approvals", show: admin || allows(CAPABILITIES.TEACHERS_MANAGE) },
        { to: "/admin/guardian-links", label: "Guardian links", show: admin || allows(CAPABILITIES.GUARDIANS_MANAGE) },
        { to: "/admin/learners", label: "Learners", show: admin || isTeacher(user) || allows(CAPABILITIES.LEARNERS_MANAGE) },
        { to: "/admin/teachers", label: "Teachers", show: admin || allows(CAPABILITIES.TEACHERS_MANAGE) },
        { to: "/admin/guardians", label: "Guardians", show: admin || allows(CAPABILITIES.GUARDIANS_MANAGE) },
      ],
    },
    {
      id: "learning",
      label: "Learning",
      items: [
        { to: "/admin/courses", label: "Courses", show: staff || allows(CAPABILITIES.COURSES_MANAGE) },
        { to: "/admin/modules", label: "Modules", show: staff || allows(CAPABILITIES.COURSES_MANAGE) },
        { to: "/admin/lessons", label: "Lessons", show: staff || allows(CAPABILITIES.COURSES_MANAGE) },
        { to: "/admin/assignments", label: "Assignments", show: staff || allows(CAPABILITIES.ASSESSMENTS_MANAGE) },
        { to: "/admin/submissions", label: "Submissions", show: staff || allows(CAPABILITIES.ASSESSMENTS_MANAGE) },
        { to: "/admin/quizzes", label: "Quizzes", show: staff || allows(CAPABILITIES.ASSESSMENTS_MANAGE) },
        { to: "/admin/questions", label: "Question bank", show: staff || allows(CAPABILITIES.ASSESSMENTS_MANAGE) },
        { to: "/admin/exams", label: "Exams", show: staff || allows(CAPABILITIES.ASSESSMENTS_MANAGE) },
        { to: "/admin/results", label: "Exam results", show: staff || allows(CAPABILITIES.ASSESSMENTS_MANAGE) },
        { to: "/admin/timetable", label: "Timetable", show: staff || allows(CAPABILITIES.ACADEMICS_MANAGE) },
        { to: "/admin/attendance", label: "Attendance", show: staff || allows(CAPABILITIES.ATTENDANCE_MANAGE) },
        { to: "/admin/curriculum", label: "Curriculum", show: teaching },
        { to: "/admin/tutor", label: "Curriculum tutor", show: staff || allows(CAPABILITIES.TUTOR_USE) },
      ],
    },
    {
      id: "operations",
      label: "School operations",
      items: [
        { to: "/admin/departments", label: "Departments", show: admin || allows(CAPABILITIES.ACADEMICS_MANAGE) },
        { to: "/admin/academic-years", label: "Academic years", show: admin || allows(CAPABILITIES.ACADEMICS_MANAGE) },
        { to: "/admin/terms", label: "Terms", show: admin || allows(CAPABILITIES.ACADEMICS_MANAGE) },
        { to: "/admin/classes", label: "Classes", show: admin || allows(CAPABILITIES.ACADEMICS_MANAGE) },
        { to: "/admin/subjects", label: "Subjects", show: admin || allows(CAPABILITIES.ACADEMICS_MANAGE) },
        { to: "/admin/fees", label: "Fees & payments", show: staff || allows(CAPABILITIES.FEES_MANAGE) },
        { to: "/admin/events", label: "School events", show: staff || allows(CAPABILITIES.ACADEMICS_MANAGE) },
        { to: "/admin/kemis", label: "KEMIS exports", show: staff || allows(CAPABILITIES.REPORTS_VIEW) },
        { to: "/admin/approval", label: "Approval review", show: staff || allows(CAPABILITIES.CONTENT_MANAGE) },
        { to: "/admin/communications", label: "Messages", show: staff || allows(CAPABILITIES.COMMUNICATIONS_MANAGE) },
        { to: "/admin/reports", label: "Reports", show: staff || allows(CAPABILITIES.REPORTS_VIEW) },
        { to: "/admin/analytics", label: "Analytics", show: staff || allows(CAPABILITIES.REPORTS_VIEW) },
      ],
    },
    {
      id: "insights",
      label: "Insights & quality",
      items: [
        { to: "/admin/early-warning", label: "Early warning", show: staff || allows(CAPABILITIES.REPORTS_VIEW) },
        { to: "/admin/fees/ledger", label: "Fee ledger & receipts", show: staff || allows(CAPABILITIES.FEES_MANAGE) },
        { to: "/admin/data-quality", label: "Data quality", show: admin || allows(CAPABILITIES.ADMIN_ACCESS) },
        { to: "/admin/audit", label: "Audit history", show: admin || allows(CAPABILITIES.ADMIN_ACCESS) },
      ],
    },
    {
      id: "system",
      label: "Content & settings",
      items: [
        { to: "/admin/textbooks", label: "Textbooks", show: staff || allows(CAPABILITIES.CONTENT_MANAGE) },
        { to: "/admin/chapters", label: "Chapters", show: content },
        { to: "/admin/resources", label: "Resources", show: content },
        { to: "/admin/resource-collections", label: "Collections", show: content },
        { to: "/admin/embed-providers", label: "Embed providers", show: content },
        { to: "/admin/school", label: "School profile", show: admin || allows(CAPABILITIES.ACADEMICS_MANAGE) },
        { to: "/admin/institutions", label: "Institutions", show: superAdmin },
        { to: "/admin/appearance", label: "Appearance", show: admin || allows(CAPABILITIES.APPEARANCE_MANAGE) },
        { to: "/admin/profile", label: "Profile" },
        { to: "/onboarding", label: "First-time setup", show: staff },
      ],
    },
  ].map((group) => ({
    ...group,
    items: group.items.filter((item) => item.show !== false),
  }));

  const activeGroup = groups.find((group) =>
    group.items.some((item) => isItemActive(item, location.pathname))
  ) || groups[0];
  const activeItem = activeGroup.items.find((item) =>
    isItemActive(item, location.pathname)
  );

  const [openGroups, setOpenGroups] = useState(() => new Set([activeGroup.id]));

  useEffect(() => {
    setOpenGroups((current) => {
      if (current.has(activeGroup.id)) return current;
      const next = new Set(current);
      next.add(activeGroup.id);
      return next;
    });
  }, [activeGroup.id]);

  function toggleGroup(id) {
    setOpenGroups((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  const closeMenu = () => setMenuOpen(false);

  async function handleLogout() {
    await signOut();
    navigate("/login");
  }

  const needle = query.trim().toLowerCase();
  const visibleGroups = needle
    ? groups
        .map((group) => ({
          ...group,
          items: group.items.filter((item) =>
            `${group.label} ${item.label}`.toLowerCase().includes(needle)
          ),
        }))
        .filter((group) => group.items.length)
    : groups;

  return (
    <div className="app-shell">
      {menuOpen && <button type="button" className="sidebar-backdrop" onClick={closeMenu} aria-label="Close navigation" />}
      <aside id="admin-sidebar" className={`app-sidebar${menuOpen ? " is-open" : ""}`}>
        <div className="admin-brand" style={{ padding: "0 0.9rem 1rem" }}>
          <img
            src={user?.institution_logo || "/mark.svg"}
            alt=""
            className="school-logo"
            onError={(event) => { event.currentTarget.src = "/mark.svg"; }}
          />
          <div>
            <div className="display" style={{ fontSize: "1.2rem", color: "var(--primary)", fontWeight: 700 }}>
              {siteContent.app.adminBrand}
            </div>
            <div className="muted" style={{ fontSize: "0.75rem" }}>
              {user?.institution_name || "Kenya · LMS + SIS + Publishing"}
            </div>
          </div>
        </div>

        <label className="sidebar-search">
          <Search size={16} strokeWidth={1.8} aria-hidden="true" />
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Find a page"
            aria-label="Find an admin page"
          />
        </label>

        <nav className="admin-nav" aria-label="Admin sections">
          {visibleGroups.map((group) => {
            const Icon = GROUP_ICONS[group.id] || SlidersHorizontal;
            const open = needle ? true : openGroups.has(group.id);
            return (
              <div
                className={`admin-nav-group${group.id === activeGroup.id ? " is-current" : ""}`}
                key={group.id}
              >
                <button
                  type="button"
                  className="admin-nav-group-button"
                  aria-expanded={open}
                  aria-controls={`admin-nav-${group.id}`}
                  onClick={() => toggleGroup(group.id)}
                >
                  <Icon size={17} strokeWidth={1.8} aria-hidden="true" />
                  <span>{group.label}</span>
                  <ChevronDown
                    size={15}
                    strokeWidth={2}
                    aria-hidden="true"
                    className={`admin-nav-chevron${open ? " is-open" : ""}`}
                  />
                </button>
                {open && (
                  <div id={`admin-nav-${group.id}`} className="admin-nav-items">
                    {group.items.map((item) => (
                      <NavItem
                        key={`${group.id}-${item.to}`}
                        to={item.to}
                        label={item.label}
                        end={item.end}
                        onNavigate={closeMenu}
                      />
                    ))}
                  </div>
                )}
              </div>
            );
          })}
          {!visibleGroups.length && (
            <p className="sidebar-empty">No pages match “{query}”.</p>
          )}
        </nav>
        <div className="admin-sidebar-footer">
          <a
            className="sidebar-live-link"
            href="/"
            target="_blank"
            rel="noopener noreferrer"
            aria-describedby="live-link-new-tab"
          >
            View live site
          </a>
          <span id="live-link-new-tab" className="sr-only">Opens in a new tab</span>
        </div>
      </aside>

      <div className="app-content">
        <header className="admin-topbar">
          <button
            className="secondary mobile-nav-toggle"
            onClick={() => setMenuOpen(!menuOpen)}
            aria-expanded={menuOpen}
            aria-controls="admin-sidebar"
          >
            {menuOpen ? "Hide menu" : "Show menu"}
          </button>
          <nav className="admin-breadcrumb" aria-label="Breadcrumb">
            <ol>
              <li>Admin</li>
              <li aria-current="page">{activeItem?.label || activeGroup.label}</li>
            </ol>
          </nav>
          <div className="admin-account">
            <div>
              <strong>{roleLabel(user)}</strong>
            </div>
            <button className="ghost small" onClick={handleLogout}>
              <LogOut size={14} strokeWidth={1.8} aria-hidden="true" /> Sign out
            </button>
          </div>
        </header>

        <main className="app-main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
