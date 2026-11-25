import { describe, it, expect } from "vitest";
import {
  ADMIN_INVITATION_ROLES, CAPABILITIES, ROLE_GROUPS, canGrantRole,
  canManageUsers, canUseAdmin, canWriteContent, canWriteTeaching,
  customRoleId, hasCapability, homeFor, isAdmin, isLearner, isPlatform,
  isSuperAdmin, isTeacher, roleLabel,
} from "./roles";

describe("role helpers", () => {
  it("keeps exactly one super-admin platform role and one admin role", () => {
    expect([...ROLE_GROUPS.PLATFORM]).toEqual(["SUPER_ADMIN"]);
    expect(ROLE_GROUPS.ADMIN).toContain("SUPER_ADMIN");
    expect(ROLE_GROUPS.ADMIN).toContain("ADMIN");
    expect(ROLE_GROUPS.ADMIN).not.toContain("PLATFORM_ADMIN");
    expect(ROLE_GROUPS.ADMIN).not.toContain("SCHOOL_ADMIN");
    expect([...ADMIN_INVITATION_ROLES]).toEqual(["ADMIN"]);
  });

  it("identifies platform admins, admins, teachers and learners", () => {
    expect(isSuperAdmin({ role: "SUPER_ADMIN" })).toBe(true);
    expect(isPlatform({ role: "SUPER_ADMIN" })).toBe(true);
    expect(isPlatform({ role: "ADMIN" })).toBe(false);
    expect(isAdmin({ role: "SUPER_ADMIN" })).toBe(true);
    expect(isAdmin({ role: "ADMIN" })).toBe(true);
    expect(isAdmin({ role: "TEACHER" })).toBe(false);
    expect(isTeacher({ role: "TEACHER" })).toBe(true);
    expect(isLearner({ role: "LEARNER" })).toBe(true);
  });

  it("treats built-in admins as unrestricted for capabilities", () => {
    for (const role of ["SUPER_ADMIN", "ADMIN"]) {
      const user = { role };
      expect(hasCapability(user, CAPABILITIES.USERS_MANAGE)).toBe(true);
      expect(hasCapability(user, CAPABILITIES.INSTITUTIONS_MANAGE)).toBe(true);
      expect(canManageUsers(user)).toBe(true);
      expect(canWriteContent(user)).toBe(true);
      expect(canWriteTeaching(user)).toBe(true);
    }
  });

  it("reads capabilities from custom users only", () => {
    const user = {
      role: "CUSTOM",
      custom_role: 9,
      custom_role_name: "Office manager",
      capabilities: [CAPABILITIES.ADMIN_ACCESS, CAPABILITIES.USERS_MANAGE],
    };
    expect(hasCapability(user, CAPABILITIES.ADMIN_ACCESS)).toBe(true);
    expect(hasCapability(user, CAPABILITIES.USERS_MANAGE)).toBe(true);
    expect(hasCapability(user, CAPABILITIES.ROLES_MANAGE)).toBe(false);
    expect(canUseAdmin(user)).toBe(true);
    expect(canManageUsers(user)).toBe(true);
    expect(canWriteTeaching(user)).toBe(false);
    expect(roleLabel(user)).toBe("Office manager");
  });

  it("hides the admin portal from custom roles without admin.access", () => {
    const user = { role: "CUSTOM", custom_role_name: "Reporter", capabilities: [CAPABILITIES.REPORTS_VIEW] };
    expect(canUseAdmin(user)).toBe(false);
    expect(hasCapability(user, CAPABILITIES.REPORTS_VIEW)).toBe(true);
    expect(homeFor(user)).toBe("/");
  });

  it("routes built-in users to the correct side", () => {
    expect(homeFor({ role: "SUPER_ADMIN" })).toBe("/admin");
    expect(homeFor({ role: "ADMIN" })).toBe("/admin");
    expect(homeFor({ role: "TEACHER" })).toBe("/admin");
    expect(homeFor({ role: "LEARNER" })).toBe("/portal");
    expect(homeFor({ role: "GUARDIAN" })).toBe("/portal");
    expect(homeFor(null)).toBe("/");
  });

  it("prevents non-super actors from granting SUPER_ADMIN", () => {
    expect(canGrantRole({ role: "SUPER_ADMIN" }, { value: "SUPER_ADMIN" })).toBe(true);
    expect(canGrantRole({ role: "ADMIN" }, { value: "SUPER_ADMIN" })).toBe(false);
    expect(canGrantRole({ role: "ADMIN" }, { value: "CUSTOM", custom_role: 4 })).toBe(true);
  });

  it("normalises custom role ids from users and role options", () => {
    expect(customRoleId(8)).toBe(8);
    expect(customRoleId({ id: 11 })).toBe(11);
    expect(customRoleId(null)).toBeNull();
  });
});
