import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./ProtectedRoute";
import { CAPABILITIES, ROLE_GROUPS } from "../utilities/roles";

const state = vi.hoisted(() => ({ signedIn: true, user: { id: 1, role: "LEARNER" } }));

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({
    user: state.signedIn ? state.user : null,
    refreshing: false,
  }),
}));

function renderGuard({ roles, capability } = {}) {
  return render(
    <MemoryRouter initialEntries={["/admin"]}>
      <Routes>
        <Route path="/" element={<div>Home page</div>} />
        <Route path="/login" element={<div>Login page</div>} />
        <Route path="/portal" element={<div>Portal page</div>} />
        <Route
          path="/admin"
          element={(
            <ProtectedRoute roles={roles} capability={capability}>
              <div>Admin page</div>
            </ProtectedRoute>
          )}
        />
      </Routes>
    </MemoryRouter>
  );
}

describe("ProtectedRoute", () => {
  afterEach(() => {
    cleanup();
    state.signedIn = true;
    state.user = { id: 1, role: "LEARNER" };
  });

  it("redirects a learner away from an admin-only route", () => {
    renderGuard({ roles: ROLE_GROUPS.ADMIN });
    expect(screen.getByText("Portal page")).toBeTruthy();
    expect(screen.queryByText("Admin page")).toBeNull();
  });

  it("allows both built-in admin roles on admin routes", () => {
    for (const role of ["SUPER_ADMIN", "ADMIN"]) {
      state.user = { id: 1, role };
      renderGuard({ roles: ROLE_GROUPS.ADMIN });
      expect(screen.getByText("Admin page")).toBeTruthy();
      cleanup();
    }
  });

  it("keeps institution management super-admin-only", () => {
    state.user = { id: 1, role: "ADMIN", capabilities: ["institutions.manage"] };
    renderGuard({ roles: ROLE_GROUPS.PLATFORM });
    expect(screen.queryByText("Admin page")).toBeNull();
    expect(screen.getByText("Home page")).toBeTruthy();

    cleanup();
    state.user = { id: 2, role: "SUPER_ADMIN" };
    renderGuard({ roles: ROLE_GROUPS.PLATFORM });
    expect(screen.getByText("Admin page")).toBeTruthy();
  });

  it("admits a custom role with the matching capability", () => {
    state.user = {
      id: 3,
      role: "CUSTOM",
      custom_role_name: "Office manager",
      capabilities: [CAPABILITIES.ADMIN_ACCESS, CAPABILITIES.USERS_MANAGE],
    };
    renderGuard({ capability: CAPABILITIES.USERS_MANAGE });
    expect(screen.getByText("Admin page")).toBeTruthy();
  });

  it("denies a custom role without the matching capability", () => {
    state.user = {
      id: 4,
      role: "CUSTOM",
      capabilities: [CAPABILITIES.ADMIN_ACCESS],
    };
    renderGuard({ capability: CAPABILITIES.USERS_MANAGE });
    expect(screen.queryByText("Admin page")).toBeNull();
    expect(screen.getByText("Home page")).toBeTruthy();
  });

  it("never unlocks admin routes for a custom role without admin.access", () => {
    state.user = {
      id: 5,
      role: "CUSTOM",
      capabilities: [CAPABILITIES.USERS_MANAGE],
    };
    renderGuard({ capability: CAPABILITIES.USERS_MANAGE });
    expect(screen.queryByText("Admin page")).toBeNull();
    expect(screen.getByText("Home page")).toBeTruthy();
  });

  it("redirects anonymous visitors to login", () => {
    state.signedIn = false;
    renderGuard();
    expect(screen.getByText("Login page")).toBeTruthy();
  });
});
