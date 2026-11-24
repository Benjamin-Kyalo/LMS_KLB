import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import AdminSignup from "./AdminSignup";

const mocks = vi.hoisted(() => ({
  api: { post: vi.fn(async () => ({ token: "session-token", user: { id: 5, role: "SCHOOL_ADMIN" } })) },
  signInWithData: vi.fn(),
}));

vi.mock("../services/api", () => ({ api: mocks.api }));
vi.mock("../context/AuthContext", () => ({ useAuth: () => ({ signInWithData: mocks.signInWithData }) }));

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/admin/signup?token=invite-token"]}>
      <Routes>
        <Route path="/admin/signup" element={<AdminSignup />} />
        <Route path="/admin" element={<div>Admin home after redemption</div>} />
      </Routes>
    </MemoryRouter>
  );
}

describe("administrator invitation redemption", () => {
  afterEach(() => {
    cleanup();
    mocks.api.post.mockClear();
    mocks.signInWithData.mockClear();
  });

  it("redeems the token and opens the admin side", async () => {
    const user = userEvent.setup();
    renderPage();

    expect(screen.getByText(/secure, single-use invitation token/)).toBeTruthy();
    expect(screen.queryByText(/signed invitation/)).toBeNull();
    expect(screen.getByLabelText(/^Invitation token/).value).toBe("invite-token");

    await user.type(screen.getByLabelText("Username"), "new_admin");
    await user.type(screen.getByLabelText("Email (must match invitation)"), "admin@example.invalid");
    await user.type(screen.getByLabelText("First name"), "New");
    await user.type(screen.getByLabelText("Last name"), "Admin");
    await user.type(screen.getByLabelText("Password"), "AdminPass123");
    await user.type(screen.getByLabelText("Confirm password"), "AdminPass123");
    await user.click(screen.getByRole("button", { name: "Create administrator account" }));

    await waitFor(() => expect(screen.getByText("Admin home after redemption")).toBeTruthy());
    expect(mocks.api.post).toHaveBeenCalledWith(
      "/auth/admin-invitations/accept/",
      expect.objectContaining({
        token: "invite-token",
        username: "new_admin",
        email: "admin@example.invalid",
      })
    );
    expect(mocks.signInWithData).toHaveBeenCalledWith({ token: "session-token", user: { id: 5, role: "SCHOOL_ADMIN" } });
  });

  it("rejects mismatched passwords before calling the API", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.type(screen.getByLabelText("Username"), "new_admin");
    await user.type(screen.getByLabelText("Email (must match invitation)"), "admin@example.invalid");
    await user.type(screen.getByLabelText("First name"), "New");
    await user.type(screen.getByLabelText("Last name"), "Admin");
    await user.type(screen.getByLabelText("Password"), "AdminPass123");
    await user.type(screen.getByLabelText("Confirm password"), "Different123");
    await user.click(screen.getByRole("button", { name: "Create administrator account" }));

    expect(await screen.findByText("Passwords do not match.")).toBeTruthy();
    expect(mocks.api.post).not.toHaveBeenCalled();
  });
});
