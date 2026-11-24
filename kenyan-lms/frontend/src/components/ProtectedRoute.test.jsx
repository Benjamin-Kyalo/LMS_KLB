import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./ProtectedRoute";

const state = vi.hoisted(() => ({ loggedIn: true, role: "LEARNER" }));

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({ user: { id: 1, role: state.role }, refreshing: false }),
}));
vi.mock("../services/auth", () => ({
  isLoggedIn: () => state.loggedIn,
}));

function renderGuard() {
  return render(
    <MemoryRouter initialEntries={["/admin"]}>
      <Routes>
        <Route path="/login" element={<div>Login page</div>} />
        <Route path="/portal" element={<div>Portal page</div>} />
        <Route
          path="/admin"
          element={<ProtectedRoute roles={["SCHOOL_ADMIN"]}><div>Admin page</div></ProtectedRoute>}
        />
      </Routes>
    </MemoryRouter>
  );
}

describe("ProtectedRoute", () => {
  afterEach(() => {
    cleanup();
    state.loggedIn = true;
    state.role = "LEARNER";
  });

  it("redirects a learner away from an admin-only route", () => {
    renderGuard();
    expect(screen.getByText("Portal page")).toBeTruthy();
    expect(screen.queryByText("Admin page")).toBeNull();
  });

  it("allows the requested role", () => {
    state.role = "SCHOOL_ADMIN";
    renderGuard();
    expect(screen.getByText("Admin page")).toBeTruthy();
  });

  it("redirects anonymous visitors to login", () => {
    state.loggedIn = false;
    renderGuard();
    expect(screen.getByText("Login page")).toBeTruthy();
  });
});
