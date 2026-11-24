import { describe, it, expect } from "vitest";
import { isPlatform, isAdmin, isTeacher, isLearner } from "./roles";

describe("role helpers", () => {
  it("identifies platform roles", () => {
    expect(isPlatform({ role: "SUPER_ADMIN" })).toBe(true);
    expect(isPlatform({ role: "TEACHER" })).toBe(false);
  });
  it("identifies admins", () => {
    expect(isAdmin({ role: "SCHOOL_ADMIN" })).toBe(true);
    expect(isAdmin({ role: "LEARNER" })).toBe(false);
  });
  it("identifies teachers and learners", () => {
    expect(isTeacher({ role: "TEACHER" })).toBe(true);
    expect(isLearner({ role: "LEARNER" })).toBe(true);
  });
});
