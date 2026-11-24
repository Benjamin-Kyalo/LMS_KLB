import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import RoleHome from "./RoleHome";

const state = vi.hoisted(() => ({ user: { id: 1, role: "SCHOOL_ADMIN" } }));

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({ user: state.user }),
}));

function renderHome(legacy = false) {
  return render(
    <MemoryRouter initialEntries={["/"]}>
      <Routes>
        <Route path="/" element={legacy
          ? <RoleHome adminTo="/custom-admin" portalTo="/custom-portal" />
          : <RoleHome />} />
        <Route path="/admin" element={<div>Admin home</div>} />
        <Route path="/portal" element={<div>Portal home</div>} />
        <Route path="/custom-admin" element={<div>Custom admin home</div>} />
        <Route path="/custom-portal" element={<div>Custom portal home</div>} />
        <Route path="/login" element={<div>Login page</div>} />
      </Routes>
    </MemoryRouter>
  );
}

describe("RoleHome", () => {
  afterEach(() => {
    cleanup();
    state.user = { id: 1, role: "SCHOOL_ADMIN" };
  });

  it("sends school and platform administrators to the admin side", () => {
    for (const role of ["SCHOOL_ADMIN", "INSTITUTION_ADMIN", "PLATFORM_ADMIN", "SUPER_ADMIN"]) {
      state.user = { id: 1, role };
      renderHome();
      expect(screen.getByText("Admin home")).toBeTruthy();
      cleanup();
    }
  });

  it("sends teachers and content managers to the admin side", () => {
    for (const role of ["TEACHER", "CONTENT_MANAGER"]) {
      state.user = { id: 1, role };
      renderHome();
      expect(screen.getByText("Admin home")).toBeTruthy();
      cleanup();
    }
  });

  it("sends learners and guardians to the user portal", () => {
    for (const role of ["LEARNER", "GUARDIAN"]) {
      state.user = { id: 2, role };
      renderHome();
      expect(screen.getByText("Portal home")).toBeTruthy();
      cleanup();
    }
  });

  it("sends anonymous visitors to sign in", () => {
    state.user = null;
    renderHome();
    expect(screen.getByText("Login page")).toBeTruthy();
  });

  it("honours custom legacy destinations", () => {
    state.user = { id: 3, role: "LEARNER" };
    renderHome(true);
    expect(screen.getByText("Custom portal home")).toBeTruthy();
    cleanup();

    state.user = { id: 4, role: "SCHOOL_ADMIN" };
    renderHome(true);
    expect(screen.getByText("Custom admin home")).toBeTruthy();
  });
});
