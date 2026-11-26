import { lazy, Suspense, useEffect, useRef } from "react";
import { BrowserRouter, Route, Routes, useLocation } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { ToastProvider } from "./context/ToastContext";
const ErrorBoundary = lazy(() => import("./components/ErrorBoundary"));
const ProtectedRoute = lazy(() => import("./components/ProtectedRoute"));
const RoleHome = lazy(() => import("./components/RoleHome"));
const DashboardLayout = lazy(() => import("./layouts/DashboardLayout"));
const PortalLayout = lazy(() => import("./layouts/PortalLayout"));
const Login = lazy(() => import("./pages/Login"));
const Home = lazy(() => import("./pages/Home"));
const Library = lazy(() => import("./pages/Library"));
const Register = lazy(() => import("./pages/Register"));
const PasswordReset = lazy(() => import("./pages/PasswordReset"));
const Onboarding = lazy(() => import("./pages/Onboarding"));
const AdminSignup = lazy(() => import("./pages/AdminSignup"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Profile = lazy(() => import("./pages/Profile"));
const SchoolProfile = lazy(() => import("./pages/SchoolProfile"));
const Institutions = lazy(() => import("./pages/Institutions"));
const Users = lazy(() => import("./pages/Users"));
const Roles = lazy(() => import("./pages/Roles"));
const AdminInvitations = lazy(() => import("./pages/AdminInvitations"));
const Departments = lazy(() => import("./pages/Departments"));
const AcademicYears = lazy(() => import("./pages/AcademicYears"));
const Terms = lazy(() => import("./pages/Terms"));
const Classes = lazy(() => import("./pages/Classes"));
const Subjects = lazy(() => import("./pages/Subjects"));
const Learners = lazy(() => import("./pages/Learners"));
const Teachers = lazy(() => import("./pages/Teachers"));
const Guardians = lazy(() => import("./pages/Guardians"));
const TeacherApprovals = lazy(() => import("./pages/TeacherApprovals"));
const GuardianLinks = lazy(() => import("./pages/GuardianLinks"));
const Courses = lazy(() => import("./pages/Courses"));
const Assignments = lazy(() => import("./pages/Assignments"));
const Submissions = lazy(() => import("./pages/Submissions"));
const Quizzes = lazy(() => import("./pages/Quizzes"));
const Modules = lazy(() => import("./pages/Modules"));
const Lessons = lazy(() => import("./pages/Lessons"));
const Questions = lazy(() => import("./pages/Questions"));
const Exams = lazy(() => import("./pages/Exams"));
const Results = lazy(() => import("./pages/Results"));
const Timetable = lazy(() => import("./pages/Timetable"));
const SchoolEvents = lazy(() => import("./pages/SchoolEvents"));
const Attendance = lazy(() => import("./pages/Attendance"));
const Curriculum = lazy(() => import("./pages/Curriculum"));
const Textbooks = lazy(() => import("./pages/Textbooks"));
const Chapters = lazy(() => import("./pages/Chapters"));
const Resources = lazy(() => import("./pages/Resources"));
const Communications = lazy(() => import("./pages/Communications"));
const Reports = lazy(() => import("./pages/Reports"));
const PortalHome = lazy(() => import("./pages/PortalHome"));
const PortalCourses = lazy(() => import("./pages/PortalCourses"));
const PortalAssignments = lazy(() => import("./pages/PortalAssignments"));
const PortalQuizzes = lazy(() => import("./pages/PortalQuizzes"));
const PortalCommunications = lazy(() => import("./pages/PortalCommunications"));
const PortalResources = lazy(() => import("./pages/PortalResources"));
const PortalDocuments = lazy(() => import("./pages/PortalDocuments"));
const ResourceCollections = lazy(() => import("./pages/ResourceCollections"));
const EmbedProviders = lazy(() => import("./pages/EmbedProviders"));
const ManagedResourcePage = lazy(() => import("./components/ManagedResourcePage"));
const FeesOverview = lazy(() => import("./pages/FeesOverview"));
const ApprovalRequests = lazy(() => import("./pages/ApprovalRequests"));
const KemisExports = lazy(() => import("./pages/KemisExports"));
const TutorWorkspace = lazy(() => import("./pages/TutorWorkspace"));
const AnalyticsOverview = lazy(() => import("./pages/AnalyticsOverview"));
const NotificationCentre = lazy(() => import("./pages/NotificationCentre"));
const EarlyWarning = lazy(() => import("./pages/EarlyWarning"));
const FeeLedger = lazy(() => import("./pages/FeeLedger"));
const DataQuality = lazy(() => import("./pages/DataQuality"));
const AuditHistory = lazy(() => import("./pages/AuditHistory"));
const AppearanceManager = lazy(() => import("./pages/AppearanceManager"));
const PortalFees = lazy(() => import("./pages/PortalFees"));
const PortalRemediation = lazy(() => import("./pages/PortalRemediation"));
const NotFound = lazy(() => import("./pages/NotFound"));
import { CAPABILITIES, ROLE_GROUPS } from "./utilities/roles";

function Guard({ roles, capability, children }) {
  return <ProtectedRoute roles={roles} capability={capability}>{children}</ProtectedRoute>;
}

// Older bookmarks still work after the split into /admin and /portal.
function Legacy({ adminTo, portalTo = "/portal" }) {
  return <RoleHome adminTo={adminTo} portalTo={portalTo} />;
}

// One keyed frame per address gives every route a short, gentle entrance.
// It also keeps the skip link pointed at the current page's main landmark and
// moves focus there after navigation so screen-reader users start in context.
function RouteFrame({ children }) {
  const location = useLocation();
  const frameRef = useRef(null);
  const firstRender = useRef(true);

  useEffect(() => {
    const frame = frameRef.current;
    if (!frame) return;

    const target = frame.querySelector("main, [role='main']") || frame;
    if (!target.id) target.id = "main-content";
    if (!target.hasAttribute("tabindex")) target.setAttribute("tabindex", "-1");

    if (firstRender.current) {
      firstRender.current = false;
      return;
    }
    target.focus({ preventScroll: true });
  }, [location.pathname, location.search]);

  return (
    <div
      ref={frameRef}
      className="route-view"
      key={`${location.pathname}${location.search}`}
    >
      {children}
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <ToastProvider>
          <BrowserRouter>
            <a className="skip-link" href="#main-content">Skip to main content</a>
            <RouteFrame>
              <Suspense fallback={<div className="panel panel-pad">Loading…</div>}>
              <Routes>
{/* lazy-loaded routes */}
              {/* Public discovery and role-based sign-in */}
              <Route path="/" element={<Home />} />
              <Route path="/home" element={<Home />} />
              <Route path="/library" element={<Library />} />
              <Route path="/register" element={<Register />} />
              <Route path="/reset-password" element={<PasswordReset />} />
              <Route path="/reset-password/:uid/:token" element={<PasswordReset />} />
              <Route path="/login" element={<Login />} />
              <Route path="/admin/login" element={<Login variant="admin" />} />
              <Route path="/admin/signup" element={<AdminSignup />} />
              <Route path="/onboarding" element={<Guard><Onboarding /></Guard>} />

              {/* Staff and administration portal */}
              <Route path="/admin" element={<Guard roles={ROLE_GROUPS.STAFF} capability={CAPABILITIES.ADMIN_ACCESS}><DashboardLayout /></Guard>}>
                <Route index element={<Dashboard />} />
                <Route path="profile" element={<Profile />} />
                <Route path="notifications" element={<Guard><NotificationCentre /></Guard>} />

                <Route path="school" element={<Guard roles={ROLE_GROUPS.ADMIN} capability={CAPABILITIES.ACADEMICS_MANAGE}><SchoolProfile /></Guard>} />
                <Route path="appearance" element={<Guard roles={ROLE_GROUPS.ADMIN} capability={CAPABILITIES.APPEARANCE_MANAGE}><AppearanceManager /></Guard>} />
                <Route path="site-content" element={<Guard roles={ROLE_GROUPS.ADMIN} capability={CAPABILITIES.APPEARANCE_MANAGE}><AppearanceManager initialTab="words" /></Guard>} />
                <Route path="theme" element={<Guard roles={ROLE_GROUPS.ADMIN} capability={CAPABILITIES.APPEARANCE_MANAGE}><AppearanceManager initialTab="palette" /></Guard>} />
                <Route path="institutions" element={<Guard roles={ROLE_GROUPS.PLATFORM}><Institutions /></Guard>} />
                <Route path="users" element={<Guard roles={ROLE_GROUPS.ADMIN} capability={CAPABILITIES.USERS_MANAGE}><Users /></Guard>} />
                <Route path="roles" element={<Guard roles={ROLE_GROUPS.ADMIN} capability={CAPABILITIES.ROLES_MANAGE}><Roles /></Guard>} />
                <Route path="invitations" element={<Guard roles={ROLE_GROUPS.ADMIN} capability={CAPABILITIES.USERS_MANAGE}><AdminInvitations /></Guard>} />
                <Route path="departments" element={<Guard roles={ROLE_GROUPS.ADMIN} capability={CAPABILITIES.ACADEMICS_MANAGE}><Departments /></Guard>} />
                <Route path="academic-years" element={<Guard roles={ROLE_GROUPS.ADMIN} capability={CAPABILITIES.ACADEMICS_MANAGE}><AcademicYears /></Guard>} />
                <Route path="terms" element={<Guard roles={ROLE_GROUPS.ADMIN} capability={CAPABILITIES.ACADEMICS_MANAGE}><Terms /></Guard>} />
                <Route path="classes" element={<Guard roles={ROLE_GROUPS.ADMIN} capability={CAPABILITIES.ACADEMICS_MANAGE}><Classes /></Guard>} />
                <Route path="subjects" element={<Guard roles={ROLE_GROUPS.ADMIN} capability={CAPABILITIES.ACADEMICS_MANAGE}><Subjects /></Guard>} />
                <Route path="learners" element={<Guard roles={ROLE_GROUPS.STAFF} capability={CAPABILITIES.LEARNERS_MANAGE}><Learners /></Guard>} />
                <Route path="teachers" element={<Guard roles={ROLE_GROUPS.ADMIN} capability={CAPABILITIES.TEACHERS_MANAGE}><Teachers /></Guard>} />
                <Route path="teacher-approvals" element={<Guard roles={ROLE_GROUPS.ADMIN} capability={CAPABILITIES.TEACHERS_MANAGE}><TeacherApprovals /></Guard>} />
                <Route path="guardians" element={<Guard roles={ROLE_GROUPS.ADMIN} capability={CAPABILITIES.GUARDIANS_MANAGE}><Guardians /></Guard>} />
                <Route path="guardian-links" element={<Guard roles={ROLE_GROUPS.ADMIN} capability={CAPABILITIES.GUARDIANS_MANAGE}><GuardianLinks /></Guard>} />

                <Route path="courses" element={<Courses />} />
                <Route path="modules" element={<Modules />} />
                <Route path="lessons" element={<Lessons />} />
                <Route path="assignments" element={<Assignments />} />
                <Route path="submissions" element={<Submissions />} />
                <Route path="quizzes" element={<Quizzes />} />
                <Route path="questions" element={<Questions />} />
                <Route path="exams" element={<Exams />} />
                <Route path="results" element={<Results />} />
                <Route path="timetable" element={<Timetable />} />
                <Route path="events" element={<SchoolEvents />} />
                <Route path="attendance" element={<Attendance />} />
                <Route path="curriculum" element={<Guard roles={ROLE_GROUPS.STAFF} capability={CAPABILITIES.COURSES_MANAGE}><Curriculum /></Guard>} />

                <Route path="textbooks" element={<Textbooks />} />
                <Route path="chapters" element={<Guard roles={ROLE_GROUPS.CONTENT} capability={CAPABILITIES.CONTENT_MANAGE}><Chapters /></Guard>} />
                <Route path="resources" element={<Guard roles={ROLE_GROUPS.CONTENT} capability={CAPABILITIES.CONTENT_MANAGE}><Resources /></Guard>} />
                <Route path="resource-collections" element={<Guard roles={ROLE_GROUPS.CONTENT} capability={CAPABILITIES.CONTENT_MANAGE}><ResourceCollections /></Guard>} />
                <Route path="embed-providers" element={<Guard roles={ROLE_GROUPS.CONTENT} capability={CAPABILITIES.CONTENT_MANAGE}><EmbedProviders /></Guard>} />

                <Route path="communications" element={<Guard roles={ROLE_GROUPS.STAFF} capability={CAPABILITIES.COMMUNICATIONS_MANAGE}><Communications /></Guard>} />
                <Route path="reports" element={<Guard roles={ROLE_GROUPS.STAFF} capability={CAPABILITIES.REPORTS_VIEW}><Reports /></Guard>} />

                {/* Extended modules: fees, review workflow, exports, tutor and analytics */}
                <Route path="fees" element={<Guard roles={ROLE_GROUPS.STAFF} capability={CAPABILITIES.FEES_MANAGE}><FeesOverview /></Guard>} />
                <Route path="fees/structures" element={<Guard roles={ROLE_GROUPS.ADMIN} capability={CAPABILITIES.FEES_MANAGE}><ManagedResourcePage title="Fee structures" overline="School office" endpoint="/fees/structures/" access="admin" columns={[{ key: "name", label: "Name" }, { key: "term_name", label: "Term" }, { key: "amount", label: "Amount" }, { key: "is_active", label: "Active", render: (r) => r.is_active ? "Yes" : "No" }]} fields={[{ name: "name", label: "Name", required: true }, { name: "term", label: "Term", type: "select", optionsEndpoint: "/institutions/terms/", labelKey: "name", required: true }, { name: "school_class", label: "Class (optional)", type: "select", optionsEndpoint: "/institutions/classes/", labelKey: "display_name" }, { name: "amount", label: "Amount (KES)", type: "number", required: true }, { name: "due_date", label: "Due date", type: "date" }, { name: "is_active", label: "Active", type: "checkbox" }]} emptyHint="Add a fee structure for a term before billing learners." /></Guard>} />
                <Route path="fees/invoices" element={<Guard roles={ROLE_GROUPS.STAFF} capability={CAPABILITIES.FEES_MANAGE}><ManagedResourcePage title="Fee invoices" overline="School office" endpoint="/fees/invoices/" access="staff" columns={[{ key: "reference", label: "Invoice" }, { key: "learner_name", label: "Learner" }, { key: "amount_due", label: "Billed" }, { key: "amount_paid", label: "Paid" }, { key: "balance", label: "Balance" }, { key: "status", label: "Status" }]} fields={[{ name: "learner", label: "Learner", type: "select", optionsEndpoint: "/learners/", labelKey: "learner_name", required: true }, { name: "fee_structure", label: "Fee structure (optional)", type: "select", optionsEndpoint: "/fees/structures/", labelKey: "name" }, { name: "amount_due", label: "Amount due (KES)", type: "number", required: true }, { name: "issue_date", label: "Issue date", type: "date", required: true }, { name: "due_date", label: "Due date", type: "date" }]} emptyHint="Create an invoice for a learner to begin recording payments." /></Guard>} />
                <Route path="fees/payments" element={<Guard roles={ROLE_GROUPS.STAFF} capability={CAPABILITIES.FEES_MANAGE}><ManagedResourcePage title="Payments" overline="School office" endpoint="/fees/payments/" access="staff" columns={[{ key: "reference", label: "Receipt" }, { key: "invoice_reference", label: "Invoice" }, { key: "amount", label: "Amount" }, { key: "method", label: "Method" }, { key: "paid_at", label: "Recorded at" }]} fields={[{ name: "invoice", label: "Invoice", type: "select", optionsEndpoint: "/fees/invoices/", labelKey: "reference", required: true }, { name: "amount", label: "Amount (KES)", type: "number", required: true }, { name: "method", label: "Method", type: "select", options: [{ value: "CASH", label: "Cash" }, { value: "BANK", label: "Bank transfer" }, { value: "MOBILE", label: "Mobile money" }, { value: "OTHER", label: "Other" }], required: true }, { name: "paid_at", label: "Paid at", type: "datetime-local", required: true }, { name: "notes", label: "Notes", type: "textarea", full: true }]} emptyHint="Record a payment against an invoice. No gateway credentials are used." /></Guard>} />

                <Route path="approval" element={<Guard roles={ROLE_GROUPS.STAFF} capability={CAPABILITIES.CONTENT_MANAGE}><ApprovalRequests /></Guard>} />
                <Route path="approval/checklist" element={<Guard roles={ROLE_GROUPS.STAFF} capability={CAPABILITIES.CONTENT_MANAGE}><ManagedResourcePage title="Approval checklist" overline="Publishing quality assurance" endpoint="/approval/checklist/" access="staff" columns={[{ key: "reference", label: "Reference" }, { key: "label", label: "Check" }, { key: "is_met", label: "Met", render: (r) => r.is_met ? "Yes" : "No" }, { key: "notes", label: "Notes" }]} fields={[{ name: "request", label: "Request", type: "select", optionsEndpoint: "/approval/requests/", labelKey: "reference", required: true }, { name: "label", label: "Check", required: true }, { name: "is_met", label: "Met", type: "checkbox" }, { name: "notes", label: "Notes", type: "textarea", full: true }]} emptyHint="Add the checks a resource must pass before review." /></Guard>} />
                <Route path="approval/decisions" element={<Guard roles={ROLE_GROUPS.STAFF} capability={CAPABILITIES.CONTENT_MANAGE}><ManagedResourcePage title="Review decisions" overline="Publishing quality assurance" endpoint="/approval/decisions/" access="readOnly" columns={[{ key: "reference", label: "Reference" }, { key: "request_title", label: "Request" }, { key: "decision", label: "Decision" }, { key: "decided_at", label: "Decided at" }, { key: "notes", label: "Notes" }]} fields={[]} emptyHint="Decisions appear here after a review is recorded." /></Guard>} />

                <Route path="kemis" element={<Guard roles={ROLE_GROUPS.STAFF} capability={CAPABILITIES.REPORTS_VIEW}><KemisExports /></Guard>} />
                <Route path="kemis/mappings" element={<Guard roles={ROLE_GROUPS.PLATFORM}><ManagedResourcePage title="KEMIS field mappings" overline="Government reporting" endpoint="/kemis/mappings/" access="platform" columns={[{ key: "dataset", label: "Dataset" }, { key: "source_field", label: "Source field" }, { key: "target_column", label: "Target column" }, { key: "is_required", label: "Required", render: (r) => r.is_required ? "Yes" : "No" }, { key: "is_active", label: "Active", render: (r) => r.is_active ? "Yes" : "No" }]} fields={[{ name: "dataset", label: "Dataset", type: "select", options: [{ value: "LEARNERS", label: "Learners" }, { value: "TEACHERS", label: "Teachers" }, { value: "INSTITUTION", label: "Institution" }, { value: "ENROLLMENT", label: "Enrolment" }, { value: "ATTENDANCE", label: "Attendance" }, { value: "RESULTS", label: "Results" }], required: true }, { name: "source_field", label: "Source field (dotted path)", required: true }, { name: "target_column", label: "Target column", required: true }, { name: "is_required", label: "Required", type: "checkbox" }, { name: "is_active", label: "Active", type: "checkbox" }, { name: "ordering", label: "Order", type: "number" }]} emptyHint="Mappings customise the default export columns." /></Guard>} />

                <Route path="tutor" element={<Guard roles={ROLE_GROUPS.STAFF} capability={CAPABILITIES.TUTOR_USE}><TutorWorkspace /></Guard>} />
                <Route path="analytics" element={<Guard roles={ROLE_GROUPS.STAFF} capability={CAPABILITIES.REPORTS_VIEW}><AnalyticsOverview /></Guard>} />
                <Route path="early-warning" element={<Guard roles={ROLE_GROUPS.STAFF} capability={CAPABILITIES.REPORTS_VIEW}><EarlyWarning /></Guard>} />
                <Route path="fees/ledger" element={<Guard roles={ROLE_GROUPS.STAFF} capability={CAPABILITIES.FEES_MANAGE}><FeeLedger /></Guard>} />
                <Route path="data-quality" element={<Guard roles={ROLE_GROUPS.ADMIN} capability={CAPABILITIES.ADMIN_ACCESS}><DataQuality /></Guard>} />
                <Route path="audit" element={<Guard roles={ROLE_GROUPS.ADMIN} capability={CAPABILITIES.ADMIN_ACCESS}><AuditHistory /></Guard>} />
                <Route path="analytics/rules" element={<Guard roles={ROLE_GROUPS.ADMIN} capability={CAPABILITIES.REPORTS_VIEW}><ManagedResourcePage title="Remediation rules" overline="Analytics" endpoint="/analytics/rules/" access="admin" columns={[{ key: "name", label: "Rule" }, { key: "mastery_below", label: "Mastery below" }, { key: "min_attempts", label: "Min attempts" }, { key: "action", label: "Action" }, { key: "is_active", label: "Active", render: (r) => r.is_active ? "Yes" : "No" }]} fields={[{ name: "name", label: "Name", required: true }, { name: "mastery_below", label: "Mastery below (0–1)", type: "number", required: true }, { name: "min_attempts", label: "Minimum attempts", type: "number" }, { name: "action", label: "Action", type: "select", options: [{ value: "PRACTICE", label: "Practice" }, { value: "RESOURCE", label: "Resource" }, { value: "COURSE", label: "Course" }, { value: "TEACHER_REVIEW", label: "Teacher review" }], required: true }, { name: "notes", label: "Notes", type: "textarea", full: true }, { name: "is_active", label: "Active", type: "checkbox" }]} emptyHint="Rules turn low mastery evidence into follow-up tasks." /></Guard>} />
                <Route path="analytics/tasks" element={<Guard roles={ROLE_GROUPS.STAFF} capability={CAPABILITIES.REPORTS_VIEW}><ManagedResourcePage title="Remediation tasks" overline="Analytics" endpoint="/analytics/tasks/" access="staff" columns={[{ key: "learner_name", label: "Learner" }, { key: "rule_name", label: "Rule" }, { key: "status", label: "Status" }, { key: "due_date", label: "Due" }]} fields={[{ name: "learner", label: "Learner", type: "select", optionsEndpoint: "/learners/", labelKey: "learner_name", required: true }, { name: "status", label: "Status", type: "select", options: [{ value: "OPEN", label: "Open" }, { value: "ASSIGNED", label: "Assigned" }, { value: "COMPLETED", label: "Completed" }, { value: "DISMISSED", label: "Dismissed" }] }, { name: "due_date", label: "Due date", type: "date" }]} emptyHint="Tasks are created by the evaluator, or can be added manually." /></Guard>} />
                <Route path="analytics/snapshots" element={<Guard roles={ROLE_GROUPS.ADMIN} capability={CAPABILITIES.REPORTS_VIEW}><ManagedResourcePage title="Analytics snapshots" overline="Analytics" endpoint="/analytics/snapshots/" access="admin" columns={[{ key: "reference", label: "Reference" }, { key: "dataset", label: "Dataset" }, { key: "period", label: "Period" }, { key: "generated_at", label: "Generated at" }]} fields={[]} emptyHint="Refresh a snapshot from the analytics overview." /></Guard>} />
              </Route>

              {/* Learner and guardian portal */}
              <Route path="/portal" element={<Guard roles={ROLE_GROUPS.PORTAL}><PortalLayout /></Guard>}>
                <Route index element={<PortalHome />} />
                <Route path="courses" element={<PortalCourses />} />
                <Route path="textbooks" element={<Textbooks resourcesTo="/portal/resources" />} />
                <Route path="resources" element={<PortalResources />} />
                <Route path="documents" element={<PortalDocuments />} />
                <Route path="assignments" element={<Guard roles={["LEARNER"]}><PortalAssignments /></Guard>} />
                <Route path="quizzes" element={<Guard roles={["LEARNER"]}><PortalQuizzes /></Guard>} />
                <Route path="reports" element={<Reports />} />
                <Route path="fees" element={<PortalFees />} />
                <Route path="tutor" element={<TutorWorkspace portal />} />
                <Route path="remediation" element={<Guard roles={["LEARNER"]}><PortalRemediation /></Guard>} />
                <Route path="communications" element={<PortalCommunications />} />
                <Route path="profile" element={<Profile />} />
                <Route path="notifications" element={<Guard><NotificationCentre /></Guard>} />
              </Route>

              {/* Redirect old page addresses instead of breaking bookmarks. */}
              <Route path="notifications" element={<Legacy adminTo="/admin/notifications" portalTo="/portal/notifications" />} />
              <Route path="dashboard" element={<Legacy adminTo="/admin" />} />
              <Route path="profile" element={<Legacy adminTo="/admin/profile" portalTo="/portal/profile" />} />
              <Route path="school" element={<Legacy adminTo="/admin/school" />} />
              <Route path="users" element={<Legacy adminTo="/admin/users" />} />
              <Route path="roles" element={<Legacy adminTo="/admin/roles" />} />
              <Route path="departments" element={<Legacy adminTo="/admin/departments" />} />
              <Route path="academic-years" element={<Legacy adminTo="/admin/academic-years" />} />
              <Route path="terms" element={<Legacy adminTo="/admin/terms" />} />
              <Route path="subjects" element={<Legacy adminTo="/admin/subjects" />} />
              <Route path="institutions" element={<Legacy adminTo="/admin/institutions" />} />
              <Route path="learners" element={<Legacy adminTo="/admin/learners" portalTo="/portal/courses" />} />
              <Route path="teachers" element={<Legacy adminTo="/admin/teachers" />} />
              <Route path="guardians" element={<Legacy adminTo="/admin/guardians" />} />
              <Route path="classes" element={<Legacy adminTo="/admin/classes" />} />
              <Route path="courses" element={<Legacy adminTo="/admin/courses" portalTo="/portal/courses" />} />
              <Route path="assignments" element={<Legacy adminTo="/admin/assignments" portalTo="/portal/assignments" />} />
              <Route path="submissions" element={<Legacy adminTo="/admin/submissions" />} />
              <Route path="quizzes" element={<Legacy adminTo="/admin/quizzes" portalTo="/portal/quizzes" />} />
              <Route path="modules" element={<Legacy adminTo="/admin/modules" />} />
              <Route path="lessons" element={<Legacy adminTo="/admin/lessons" />} />
              <Route path="questions" element={<Legacy adminTo="/admin/questions" />} />
              <Route path="results" element={<Legacy adminTo="/admin/results" />} />
              <Route path="timetable" element={<Legacy adminTo="/admin/timetable" />} />
              <Route path="events" element={<Legacy adminTo="/admin/events" />} />
              <Route path="chapters" element={<Legacy adminTo="/admin/chapters" />} />
              <Route path="resources" element={<Legacy adminTo="/admin/resources" portalTo="/portal/resources" />} />
              <Route path="exams" element={<Legacy adminTo="/admin/exams" />} />
              <Route path="attendance" element={<Legacy adminTo="/admin/attendance" />} />
              <Route path="curriculum" element={<Legacy adminTo="/admin/curriculum" />} />
              <Route path="textbooks" element={<Legacy adminTo="/admin/textbooks" portalTo="/portal/textbooks" />} />
              <Route path="communications" element={<Legacy adminTo="/admin/communications" portalTo="/portal/communications" />} />
              <Route path="reports" element={<Legacy adminTo="/admin/reports" portalTo="/portal/reports" />} />

                <Route path="*" element={<NotFound />} />
              </Routes>
              </Suspense>
            </RouteFrame>
          </BrowserRouter>
        </ToastProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}
