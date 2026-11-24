import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { ToastProvider } from "./context/ToastContext";
import ErrorBoundary from "./components/ErrorBoundary";
import ProtectedRoute from "./components/ProtectedRoute";
import RoleHome from "./components/RoleHome";
import DashboardLayout from "./layouts/DashboardLayout";
import PortalLayout from "./layouts/PortalLayout";
import Login from "./pages/Login";
import Home from "./pages/Home";
import Register from "./pages/Register";
import AdminSignup from "./pages/AdminSignup";
import Dashboard from "./pages/Dashboard";
import Profile from "./pages/Profile";
import SchoolProfile from "./pages/SchoolProfile";
import Institutions from "./pages/Institutions";
import Users from "./pages/Users";
import Roles from "./pages/Roles";
import AdminInvitations from "./pages/AdminInvitations";
import Departments from "./pages/Departments";
import AcademicYears from "./pages/AcademicYears";
import Terms from "./pages/Terms";
import Classes from "./pages/Classes";
import Subjects from "./pages/Subjects";
import Learners from "./pages/Learners";
import Teachers from "./pages/Teachers";
import Guardians from "./pages/Guardians";
import Courses from "./pages/Courses";
import Assignments from "./pages/Assignments";
import Submissions from "./pages/Submissions";
import Quizzes from "./pages/Quizzes";
import Modules from "./pages/Modules";
import Lessons from "./pages/Lessons";
import Questions from "./pages/Questions";
import Exams from "./pages/Exams";
import Results from "./pages/Results";
import Timetable from "./pages/Timetable";
import SchoolEvents from "./pages/SchoolEvents";
import Attendance from "./pages/Attendance";
import Curriculum from "./pages/Curriculum";
import Textbooks from "./pages/Textbooks";
import Chapters from "./pages/Chapters";
import Resources from "./pages/Resources";
import Communications from "./pages/Communications";
import Reports from "./pages/Reports";
import PortalHome from "./pages/PortalHome";
import PortalCourses from "./pages/PortalCourses";
import PortalAssignments from "./pages/PortalAssignments";
import PortalQuizzes from "./pages/PortalQuizzes";
import PortalCommunications from "./pages/PortalCommunications";
import PortalResources from "./pages/PortalResources";
import ManagedResourcePage from "./components/ManagedResourcePage";
import FeesOverview from "./pages/FeesOverview";
import ApprovalRequests from "./pages/ApprovalRequests";
import KemisExports from "./pages/KemisExports";
import TutorWorkspace from "./pages/TutorWorkspace";
import AnalyticsOverview from "./pages/AnalyticsOverview";
import SyncQueue from "./pages/SyncQueue";
import PortalFees from "./pages/PortalFees";
import PortalRemediation from "./pages/PortalRemediation";
import NotFound from "./pages/NotFound";
import { ROLE_GROUPS } from "./utilities/roles";

function Guard({ roles, children }) {
  return <ProtectedRoute roles={roles}>{children}</ProtectedRoute>;
}

// Older bookmarks still work after the split into /admin and /portal.
function Legacy({ adminTo, portalTo = "/portal" }) {
  return <RoleHome adminTo={adminTo} portalTo={portalTo} />;
}

export default function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <ToastProvider>
          <BrowserRouter>
            <Routes>
              {/* Public discovery and role-based sign-in */}
              <Route path="/" element={<Home />} />
              <Route path="/home" element={<Home />} />
              <Route path="/register" element={<Register />} />
              <Route path="/login" element={<Login />} />
              <Route path="/admin/login" element={<Login variant="admin" />} />
              <Route path="/admin/signup" element={<AdminSignup />} />

              {/* Staff and administration portal */}
              <Route path="/admin" element={<Guard roles={ROLE_GROUPS.STAFF}><DashboardLayout /></Guard>}>
                <Route index element={<Dashboard />} />
                <Route path="profile" element={<Profile />} />

                <Route path="school" element={<Guard roles={ROLE_GROUPS.ADMIN}><SchoolProfile /></Guard>} />
                <Route path="institutions" element={<Guard roles={ROLE_GROUPS.PLATFORM}><Institutions /></Guard>} />
                <Route path="users" element={<Guard roles={ROLE_GROUPS.ADMIN}><Users /></Guard>} />
                <Route path="roles" element={<Guard roles={ROLE_GROUPS.ADMIN}><Roles /></Guard>} />
                <Route path="invitations" element={<Guard roles={ROLE_GROUPS.ADMIN}><AdminInvitations /></Guard>} />
                <Route path="departments" element={<Guard roles={ROLE_GROUPS.ADMIN}><Departments /></Guard>} />
                <Route path="academic-years" element={<Guard roles={ROLE_GROUPS.ADMIN}><AcademicYears /></Guard>} />
                <Route path="terms" element={<Guard roles={ROLE_GROUPS.ADMIN}><Terms /></Guard>} />
                <Route path="classes" element={<Guard roles={ROLE_GROUPS.ADMIN}><Classes /></Guard>} />
                <Route path="subjects" element={<Guard roles={ROLE_GROUPS.ADMIN}><Subjects /></Guard>} />
                <Route path="learners" element={<Guard roles={ROLE_GROUPS.STAFF}><Learners /></Guard>} />
                <Route path="teachers" element={<Guard roles={ROLE_GROUPS.ADMIN}><Teachers /></Guard>} />
                <Route path="guardians" element={<Guard roles={ROLE_GROUPS.ADMIN}><Guardians /></Guard>} />

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
                <Route path="curriculum" element={<Guard roles={ROLE_GROUPS.STAFF}><Curriculum /></Guard>} />

                <Route path="textbooks" element={<Textbooks />} />
                <Route path="chapters" element={<Guard roles={ROLE_GROUPS.CONTENT}><Chapters /></Guard>} />
                <Route path="resources" element={<Guard roles={ROLE_GROUPS.CONTENT}><Resources /></Guard>} />

                <Route path="communications" element={<Guard roles={ROLE_GROUPS.STAFF}><Communications /></Guard>} />
                <Route path="reports" element={<Guard roles={ROLE_GROUPS.STAFF}><Reports /></Guard>} />

                {/* Extended modules: fees, review workflow, exports, tutor and analytics */}
                <Route path="fees" element={<Guard roles={ROLE_GROUPS.STAFF}><FeesOverview /></Guard>} />
                <Route path="fees/structures" element={<Guard roles={ROLE_GROUPS.ADMIN}><ManagedResourcePage title="Fee structures" overline="School office" endpoint="/fees/structures/" access="admin" columns={[{ key: "name", label: "Name" }, { key: "term_name", label: "Term" }, { key: "amount", label: "Amount" }, { key: "is_active", label: "Active", render: (r) => r.is_active ? "Yes" : "No" }]} fields={[{ name: "name", label: "Name", required: true }, { name: "term", label: "Term", type: "select", optionsEndpoint: "/institutions/terms/", labelKey: "name", required: true }, { name: "school_class", label: "Class (optional)", type: "select", optionsEndpoint: "/institutions/classes/", labelKey: "name" }, { name: "amount", label: "Amount (KES)", type: "number", required: true }, { name: "due_date", label: "Due date", type: "date" }, { name: "is_active", label: "Active", type: "checkbox" }]} emptyHint="Add a fee structure for a term before billing learners." /></Guard>} />
                <Route path="fees/invoices" element={<Guard roles={ROLE_GROUPS.STAFF}><ManagedResourcePage title="Fee invoices" overline="School office" endpoint="/fees/invoices/" access="staff" columns={[{ key: "reference", label: "Invoice" }, { key: "learner_name", label: "Learner" }, { key: "amount_due", label: "Billed" }, { key: "amount_paid", label: "Paid" }, { key: "balance", label: "Balance" }, { key: "status", label: "Status" }]} fields={[{ name: "learner", label: "Learner", type: "select", optionsEndpoint: "/learners/", labelKey: "learner_name", required: true }, { name: "fee_structure", label: "Fee structure (optional)", type: "select", optionsEndpoint: "/fees/structures/", labelKey: "name" }, { name: "amount_due", label: "Amount due (KES)", type: "number", required: true }, { name: "issue_date", label: "Issue date", type: "date", required: true }, { name: "due_date", label: "Due date", type: "date" }]} emptyHint="Create an invoice for a learner to begin recording payments." /></Guard>} />
                <Route path="fees/payments" element={<Guard roles={ROLE_GROUPS.STAFF}><ManagedResourcePage title="Payments" overline="School office" endpoint="/fees/payments/" access="staff" columns={[{ key: "reference", label: "Receipt" }, { key: "invoice_reference", label: "Invoice" }, { key: "amount", label: "Amount" }, { key: "method", label: "Method" }, { key: "paid_at", label: "Recorded at" }]} fields={[{ name: "invoice", label: "Invoice", type: "select", optionsEndpoint: "/fees/invoices/", labelKey: "reference", required: true }, { name: "amount", label: "Amount (KES)", type: "number", required: true }, { name: "method", label: "Method", type: "select", options: [{ value: "CASH", label: "Cash" }, { value: "BANK", label: "Bank transfer" }, { value: "MOBILE", label: "Mobile money" }, { value: "OTHER", label: "Other" }], required: true }, { name: "paid_at", label: "Paid at", type: "datetime-local", required: true }, { name: "notes", label: "Notes", type: "textarea", full: true }]} emptyHint="Record a payment against an invoice. No gateway credentials are used." /></Guard>} />

                <Route path="approval" element={<Guard roles={ROLE_GROUPS.STAFF}><ApprovalRequests /></Guard>} />
                <Route path="approval/checklist" element={<Guard roles={ROLE_GROUPS.STAFF}><ManagedResourcePage title="Approval checklist" overline="Publishing quality assurance" endpoint="/approval/checklist/" access="staff" columns={[{ key: "reference", label: "Reference" }, { key: "label", label: "Check" }, { key: "is_met", label: "Met", render: (r) => r.is_met ? "Yes" : "No" }, { key: "notes", label: "Notes" }]} fields={[{ name: "request", label: "Request", type: "select", optionsEndpoint: "/approval/requests/", labelKey: "reference", required: true }, { name: "label", label: "Check", required: true }, { name: "is_met", label: "Met", type: "checkbox" }, { name: "notes", label: "Notes", type: "textarea", full: true }]} emptyHint="Add the checks a resource must pass before review." /></Guard>} />
                <Route path="approval/decisions" element={<Guard roles={ROLE_GROUPS.STAFF}><ManagedResourcePage title="Review decisions" overline="Publishing quality assurance" endpoint="/approval/decisions/" access="readOnly" columns={[{ key: "reference", label: "Reference" }, { key: "request_title", label: "Request" }, { key: "decision", label: "Decision" }, { key: "decided_at", label: "Decided at" }, { key: "notes", label: "Notes" }]} fields={[]} emptyHint="Decisions appear here after a review is recorded." /></Guard>} />

                <Route path="kemis" element={<Guard roles={ROLE_GROUPS.STAFF}><KemisExports /></Guard>} />
                <Route path="kemis/mappings" element={<Guard roles={ROLE_GROUPS.PLATFORM}><ManagedResourcePage title="KEMIS field mappings" overline="Government reporting" endpoint="/kemis/mappings/" access="platform" columns={[{ key: "dataset", label: "Dataset" }, { key: "source_field", label: "Source field" }, { key: "target_column", label: "Target column" }, { key: "is_required", label: "Required", render: (r) => r.is_required ? "Yes" : "No" }, { key: "is_active", label: "Active", render: (r) => r.is_active ? "Yes" : "No" }]} fields={[{ name: "dataset", label: "Dataset", type: "select", options: [{ value: "LEARNERS", label: "Learners" }, { value: "TEACHERS", label: "Teachers" }, { value: "INSTITUTION", label: "Institution" }, { value: "ENROLLMENT", label: "Enrolment" }, { value: "ATTENDANCE", label: "Attendance" }, { value: "RESULTS", label: "Results" }], required: true }, { name: "source_field", label: "Source field (dotted path)", required: true }, { name: "target_column", label: "Target column", required: true }, { name: "is_required", label: "Required", type: "checkbox" }, { name: "is_active", label: "Active", type: "checkbox" }, { name: "ordering", label: "Order", type: "number" }]} emptyHint="Mappings customise the default export columns." /></Guard>} />

                <Route path="tutor" element={<Guard roles={ROLE_GROUPS.STAFF}><TutorWorkspace /></Guard>} />
                <Route path="analytics" element={<Guard roles={ROLE_GROUPS.STAFF}><AnalyticsOverview /></Guard>} />
                <Route path="analytics/rules" element={<Guard roles={ROLE_GROUPS.ADMIN}><ManagedResourcePage title="Remediation rules" overline="Analytics" endpoint="/analytics/rules/" access="admin" columns={[{ key: "name", label: "Rule" }, { key: "mastery_below", label: "Mastery below" }, { key: "min_attempts", label: "Min attempts" }, { key: "action", label: "Action" }, { key: "is_active", label: "Active", render: (r) => r.is_active ? "Yes" : "No" }]} fields={[{ name: "name", label: "Name", required: true }, { name: "mastery_below", label: "Mastery below (0–1)", type: "number", required: true }, { name: "min_attempts", label: "Minimum attempts", type: "number" }, { name: "action", label: "Action", type: "select", options: [{ value: "PRACTICE", label: "Practice" }, { value: "RESOURCE", label: "Resource" }, { value: "COURSE", label: "Course" }, { value: "TEACHER_REVIEW", label: "Teacher review" }], required: true }, { name: "notes", label: "Notes", type: "textarea", full: true }, { name: "is_active", label: "Active", type: "checkbox" }]} emptyHint="Rules turn low mastery evidence into follow-up tasks." /></Guard>} />
                <Route path="analytics/tasks" element={<Guard roles={ROLE_GROUPS.STAFF}><ManagedResourcePage title="Remediation tasks" overline="Analytics" endpoint="/analytics/tasks/" access="staff" columns={[{ key: "learner_name", label: "Learner" }, { key: "rule_name", label: "Rule" }, { key: "status", label: "Status" }, { key: "due_date", label: "Due" }]} fields={[{ name: "learner", label: "Learner", type: "select", optionsEndpoint: "/learners/", labelKey: "learner_name", required: true }, { name: "status", label: "Status", type: "select", options: [{ value: "OPEN", label: "Open" }, { value: "ASSIGNED", label: "Assigned" }, { value: "COMPLETED", label: "Completed" }, { value: "DISMISSED", label: "Dismissed" }] }, { name: "due_date", label: "Due date", type: "date" }]} emptyHint="Tasks are created by the evaluator, or can be added manually." /></Guard>} />
                <Route path="analytics/snapshots" element={<Guard roles={ROLE_GROUPS.ADMIN}><ManagedResourcePage title="Analytics snapshots" overline="Analytics" endpoint="/analytics/snapshots/" access="admin" columns={[{ key: "reference", label: "Reference" }, { key: "dataset", label: "Dataset" }, { key: "period", label: "Period" }, { key: "generated_at", label: "Generated at" }]} fields={[]} emptyHint="Refresh a snapshot from the analytics overview." /></Guard>} />

                <Route path="sync" element={<Guard roles={ROLE_GROUPS.STAFF}><SyncQueue /></Guard>} />
              </Route>

              {/* Learner and guardian portal */}
              <Route path="/portal" element={<Guard roles={ROLE_GROUPS.PORTAL}><PortalLayout /></Guard>}>
                <Route index element={<PortalHome />} />
                <Route path="courses" element={<PortalCourses />} />
                <Route path="textbooks" element={<Textbooks resourcesTo="/portal/resources" />} />
                <Route path="resources" element={<PortalResources />} />
                <Route path="assignments" element={<Guard roles={["LEARNER"]}><PortalAssignments /></Guard>} />
                <Route path="quizzes" element={<Guard roles={["LEARNER"]}><PortalQuizzes /></Guard>} />
                <Route path="reports" element={<Reports />} />
                <Route path="fees" element={<PortalFees />} />
                <Route path="tutor" element={<TutorWorkspace portal />} />
                <Route path="remediation" element={<Guard roles={["LEARNER"]}><PortalRemediation /></Guard>} />
                <Route path="communications" element={<PortalCommunications />} />
                <Route path="sync" element={<SyncQueue />} />
                <Route path="profile" element={<Profile />} />
              </Route>

              {/* Redirect old page addresses instead of breaking bookmarks. */}
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
          </BrowserRouter>
        </ToastProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}
