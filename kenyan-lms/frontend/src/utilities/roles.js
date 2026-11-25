// One source of truth for role labels and client-side access checks.
// These checks only shape the UI; the Django API repeats and enforces them.

export const ROLES = {
  SUPER_ADMIN: "Platform Super Administrator",
  ADMIN: "Administrator",
  CUSTOM: "Custom role",
  TEACHER: "Teacher",
  LEARNER: "Learner",
  GUARDIAN: "Parent / Guardian",
};

export const CAPABILITIES = {
  ADMIN_ACCESS: "admin.access",
  USERS_MANAGE: "users.manage",
  ROLES_MANAGE: "roles.manage",
  ACADEMICS_MANAGE: "academics.manage",
  LEARNERS_MANAGE: "learners.manage",
  TEACHERS_MANAGE: "teachers.manage",
  GUARDIANS_MANAGE: "guardians.manage",
  COURSES_MANAGE: "courses.manage",
  ASSESSMENTS_MANAGE: "assessments.manage",
  CONTENT_MANAGE: "content.manage",
  ATTENDANCE_MANAGE: "attendance.manage",
  FEES_MANAGE: "fees.manage",
  COMMUNICATIONS_MANAGE: "communications.manage",
  REPORTS_VIEW: "reports.view",
  APPEARANCE_MANAGE: "appearance.manage",
  INSTITUTIONS_MANAGE: "institutions.manage",
  TUTOR_USE: "tutor.use",
};

export const CAPABILITY_LABELS = {
  [CAPABILITIES.ADMIN_ACCESS]: "Admin portal access",
  [CAPABILITIES.USERS_MANAGE]: "Manage users",
  [CAPABILITIES.ROLES_MANAGE]: "Manage roles",
  [CAPABILITIES.ACADEMICS_MANAGE]: "Manage academics",
  [CAPABILITIES.LEARNERS_MANAGE]: "Manage learners",
  [CAPABILITIES.TEACHERS_MANAGE]: "Manage teachers",
  [CAPABILITIES.GUARDIANS_MANAGE]: "Manage guardians",
  [CAPABILITIES.COURSES_MANAGE]: "Manage courses",
  [CAPABILITIES.ASSESSMENTS_MANAGE]: "Manage assessments",
  [CAPABILITIES.CONTENT_MANAGE]: "Manage content",
  [CAPABILITIES.ATTENDANCE_MANAGE]: "Manage attendance",
  [CAPABILITIES.FEES_MANAGE]: "Manage fees",
  [CAPABILITIES.COMMUNICATIONS_MANAGE]: "Manage communications",
  [CAPABILITIES.REPORTS_VIEW]: "View reports",
  [CAPABILITIES.APPEARANCE_MANAGE]: "Manage appearance",
  [CAPABILITIES.INSTITUTIONS_MANAGE]: "Manage institutions",
  [CAPABILITIES.TUTOR_USE]: "Use curriculum tutor",
};

// Grouped for the role editor. Every capability appears in exactly one group.
export const CAPABILITY_GROUPS = [
  {
    id: "access",
    label: "Access & settings",
    capabilities: [
      CAPABILITIES.ADMIN_ACCESS,
      CAPABILITIES.USERS_MANAGE,
      CAPABILITIES.ROLES_MANAGE,
      CAPABILITIES.APPEARANCE_MANAGE,
      CAPABILITIES.INSTITUTIONS_MANAGE,
    ],
  },
  {
    id: "people",
    label: "People",
    capabilities: [
      CAPABILITIES.LEARNERS_MANAGE,
      CAPABILITIES.TEACHERS_MANAGE,
      CAPABILITIES.GUARDIANS_MANAGE,
    ],
  },
  {
    id: "learning",
    label: "Learning & content",
    capabilities: [
      CAPABILITIES.ACADEMICS_MANAGE,
      CAPABILITIES.COURSES_MANAGE,
      CAPABILITIES.ASSESSMENTS_MANAGE,
      CAPABILITIES.CONTENT_MANAGE,
    ],
  },
  {
    id: "operations",
    label: "School operations",
    capabilities: [
      CAPABILITIES.ATTENDANCE_MANAGE,
      CAPABILITIES.FEES_MANAGE,
      CAPABILITIES.COMMUNICATIONS_MANAGE,
    ],
  },
  {
    id: "insights",
    label: "Insights & tools",
    capabilities: [CAPABILITIES.REPORTS_VIEW, CAPABILITIES.TUTOR_USE],
  },
];

export const SUPER_ADMIN_ROLES = new Set(["SUPER_ADMIN"]);
export const ADMIN_ROLES = new Set(["SUPER_ADMIN", "ADMIN"]);
export const STAFF_ROLES = new Set(["SUPER_ADMIN", "ADMIN", "TEACHER"]);
export const PORTAL_ROLES = new Set(["LEARNER", "GUARDIAN"]);
export const PUBLIC_REGISTRATION_ROLES = new Set(["LEARNER", "GUARDIAN", "TEACHER"]);
// Administrator invitations fix a built-in admin role; custom roles are assigned
// on the Users screen. A super admin can additionally issue SUPER_ADMIN.
export const ADMIN_INVITATION_ROLES = new Set(["ADMIN"]);

// Kept as an alias because platform-only checks still read naturally this way.
export const PLATFORM_ROLES = SUPER_ADMIN_ROLES;

export const ROLE_GROUPS = {
  // Platform-only: institution management and other global settings.
  PLATFORM: [...SUPER_ADMIN_ROLES],
  // Institutional administration: super admins and admins.
  ADMIN: [...ADMIN_ROLES],
  STAFF: [...STAFF_ROLES],
  PORTAL: [...PORTAL_ROLES],
  CONTENT: [...ADMIN_ROLES],
};

export const BUILT_IN_ROLES = [
  {
    value: "SUPER_ADMIN",
    label: ROLES.SUPER_ADMIN,
    description: "Unrestricted platform-wide access, including institution management.",
    capabilitySummary: "All capabilities",
  },
  {
    value: "ADMIN",
    label: ROLES.ADMIN,
    description: "Unrestricted CRUD inside its own institution.",
    capabilitySummary: "All institutional capabilities",
  },
  {
    value: "CUSTOM",
    label: ROLES.CUSTOM,
    description: "A named, reusable role with a selected set of capabilities.",
    capabilitySummary: "Configured capabilities",
  },
  {
    value: "TEACHER",
    label: ROLES.TEACHER,
    description: "Teaching, assessment and classroom workflows.",
    capabilitySummary: "Teaching workflows",
  },
  {
    value: "LEARNER",
    label: ROLES.LEARNER,
    description: "Learner portal access.",
    capabilitySummary: "Portal only",
  },
  {
    value: "GUARDIAN",
    label: ROLES.GUARDIAN,
    description: "Parent / guardian portal access.",
    capabilitySummary: "Portal only",
  },
];

export function hasRole(user, allowed) {
  if (!user || !allowed) return false;
  if (allowed instanceof Set) return allowed.has(user.role);
  return allowed.includes(user.role);
}

export function isSuperAdmin(user) { return user?.role === "SUPER_ADMIN"; }
export function isAdmin(user) { return user?.role === "SUPER_ADMIN" || user?.role === "ADMIN"; }
export function isCustomRole(user) { return user?.role === "CUSTOM"; }
export function isPlatform(user) { return isSuperAdmin(user); }
export function isSchoolAdmin(user) { return isAdmin(user); }
export function isTeacher(user) { return user?.role === "TEACHER"; }
export function isLearner(user) { return user?.role === "LEARNER"; }
export function isGuardian(user) { return user?.role === "GUARDIAN"; }

// Built-in admins are unrestricted. Custom roles carry their capabilities on
// the user object returned by the API; every other role has no admin capability.
export function hasCapability(user, capability) {
  if (!user || !capability) return false;
  if (isAdmin(user)) return true;
  if (!isCustomRole(user)) return false;
  return Array.isArray(user.capabilities) && user.capabilities.includes(capability);
}

// A custom role only sees the admin portal when its capabilities include
// admin.access. Built-in teachers keep their existing staff access.
export function canUseAdmin(user) {
  if (isAdmin(user) || isTeacher(user)) return true;
  return isCustomRole(user) && hasCapability(user, CAPABILITIES.ADMIN_ACCESS);
}

export function canUsePortal(user) { return hasRole(user, PORTAL_ROLES); }

export function canManageUsers(user) {
  return isAdmin(user) || (canUseAdmin(user) && hasCapability(user, CAPABILITIES.USERS_MANAGE));
}

export function canManagePlatform(user) { return isSuperAdmin(user); }

export function canWriteContent(user) {
  return isAdmin(user) || (canUseAdmin(user) && hasCapability(user, CAPABILITIES.CONTENT_MANAGE));
}

export function canWriteTeaching(user) {
  if (isAdmin(user) || isTeacher(user)) return true;
  return canUseAdmin(user) && (
    hasCapability(user, CAPABILITIES.COURSES_MANAGE) ||
    hasCapability(user, CAPABILITIES.ASSESSMENTS_MANAGE)
  );
}

// Match the API's role-assignment rules so the picker never offers an option
// the server would reject.
export function canGrantRole(actor, option) {
  if (!option || !option.value) return false;
  if (isSuperAdmin(actor)) return true;
  if (isAdmin(actor)) return option.value !== "SUPER_ADMIN";
  if (!isCustomRole(actor) || !hasCapability(actor, CAPABILITIES.USERS_MANAGE)) return false;
  if (option.value === "CUSTOM") return hasCapability(actor, CAPABILITIES.ROLES_MANAGE);
  return ["TEACHER", "LEARNER", "GUARDIAN"].includes(option.value);
}

export function customRoleId(value) {
  if (value && typeof value === "object") return value.id ?? value.custom_role ?? null;
  return value ?? null;
}

export function roleLabel(user) {
  if (!user) return "";
  if (user.role === "CUSTOM") return user.custom_role_name || ROLES.CUSTOM;
  return ROLES[user.role] || user.role || "";
}

export function homeFor(user) {
  if (canUsePortal(user)) return "/portal";
  if (canUseAdmin(user)) return "/admin";
  return "/";
}
