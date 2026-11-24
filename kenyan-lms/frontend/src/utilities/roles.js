// One source of truth for role labels and client-side access checks.
// These checks only shape the UI; the Django API repeats and enforces them.

export const ROLES = {
  SUPER_ADMIN: "Platform Super Administrator",
  PLATFORM_ADMIN: "Platform Administrator",
  INSTITUTION_ADMIN: "Institution Administrator",
  SCHOOL_ADMIN: "School Administrator",
  TEACHER: "Teacher",
  LEARNER: "Learner",
  GUARDIAN: "Parent / Guardian",
  CONTENT_MANAGER: "Content Manager",
};

export const PLATFORM_ROLES = new Set(["SUPER_ADMIN", "PLATFORM_ADMIN"]);
export const SCHOOL_ADMIN_ROLES = new Set(["INSTITUTION_ADMIN", "SCHOOL_ADMIN"]);
export const INSTITUTION_ADMIN_ROLES = new Set([...PLATFORM_ROLES, ...SCHOOL_ADMIN_ROLES]);
export const STAFF_ROLES = new Set([...INSTITUTION_ADMIN_ROLES, "TEACHER", "CONTENT_MANAGER"]);
export const PORTAL_ROLES = new Set(["LEARNER", "GUARDIAN"]);
export const PUBLIC_REGISTRATION_ROLES = new Set(["LEARNER", "GUARDIAN", "TEACHER"]);
export const ADMIN_INVITATION_ROLES = SCHOOL_ADMIN_ROLES;

export const ROLE_GROUPS = {
  PLATFORM: [...PLATFORM_ROLES],
  ADMIN: [...INSTITUTION_ADMIN_ROLES],
  SCHOOL_ADMIN: [...SCHOOL_ADMIN_ROLES],
  STAFF: [...STAFF_ROLES],
  PORTAL: [...PORTAL_ROLES],
  CONTENT: [...PLATFORM_ROLES, "CONTENT_MANAGER"],
};

export function hasRole(user, allowed) {
  if (!user || !allowed) return false;
  if (allowed instanceof Set) return allowed.has(user.role);
  return allowed.includes(user.role);
}

export function isPlatform(user) { return hasRole(user, PLATFORM_ROLES); }
export function isSchoolAdmin(user) { return hasRole(user, SCHOOL_ADMIN_ROLES); }
export function isAdmin(user) { return hasRole(user, INSTITUTION_ADMIN_ROLES); }
export function isTeacher(user) { return user && user.role === "TEACHER"; }
export function isLearner(user) { return user && user.role === "LEARNER"; }
export function isGuardian(user) { return user && user.role === "GUARDIAN"; }
export function isContentManager(user) { return user && user.role === "CONTENT_MANAGER"; }

export function canManageUsers(user) { return isAdmin(user); }
export function canManagePlatform(user) { return isPlatform(user); }
export function canWriteContent(user) { return isPlatform(user) || isContentManager(user); }
export function canWriteTeaching(user) { return isAdmin(user) || isTeacher(user); }

export function canUseAdmin(user) { return hasRole(user, STAFF_ROLES); }
export function canUsePortal(user) { return hasRole(user, PORTAL_ROLES); }

export function homeFor(user) {
  if (canUsePortal(user)) return "/portal";
  if (canUseAdmin(user)) return "/admin";
  return "/";
}
