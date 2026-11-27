import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import DashboardLayout from "./DashboardLayout";

const mocks = vi.hoisted(() => ({ user: { id: 1, role: "SUPER_ADMIN" } }));

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({ user: mocks.user, signOut: vi.fn(async () => {}) }),
}));
vi.mock("../context/SiteContentContext", () => ({
  useSiteContent: () => ({ content: { app: { adminBrand: "KLB Elimu" } } }),
}));

function renderLayout() {
  return render(<MemoryRouter initialEntries={["/admin"]}><DashboardLayout /></MemoryRouter>);
}

function linkFor(label) {
  fireEvent.change(screen.getByLabelText("Find an admin page"), { target: { value: label } });
  return screen.queryByRole("link", { name: label });
}

describe("DashboardLayout capability navigation", () => {
  afterEach(() => {
    cleanup();
    mocks.user = { id: 1, role: "SUPER_ADMIN" };
  });

  it("shows platform links only to a super admin", () => {
    renderLayout();
    expect(linkFor("Roles")).toBeTruthy();
    expect(linkFor("Institutions")).toBeTruthy();
  });

  it("shows admin links but no institution management to an admin", () => {
    mocks.user = { id: 2, role: "ADMIN" };
    renderLayout();
    expect(linkFor("Roles")).toBeTruthy();
    expect(linkFor("Institutions")).toBeNull();
  });

  it("shows only capability-enabled links to a custom admin", () => {
    mocks.user = {
      id: 3,
      role: "CUSTOM",
      custom_role_name: "Office manager",
      capabilities: ["admin.access", "users.manage"],
    };
    renderLayout();
    expect(screen.getByText("Office manager")).toBeTruthy();
    expect(linkFor("Users")).toBeTruthy();
    expect(linkFor("Roles")).toBeNull();
    expect(linkFor("Institutions")).toBeNull();
    expect(linkFor("Resources")).toBeNull();
    expect(linkFor("Courses")).toBeNull();
  });

  it("hides admin pages from a custom role without admin.access", () => {
    mocks.user = {
      id: 4,
      role: "CUSTOM",
      custom_role_name: "Reporter",
      capabilities: ["reports.view", "users.manage"],
    };
    renderLayout();
    expect(linkFor("Users")).toBeNull();
    expect(linkFor("Roles")).toBeNull();
    expect(linkFor("Reports")).toBeNull();
  });
});
