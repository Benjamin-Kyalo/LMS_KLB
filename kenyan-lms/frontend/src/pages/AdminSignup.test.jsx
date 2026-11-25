import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import AdminSignup from "./AdminSignup";

const mocks = vi.hoisted(() => ({
  api: { post: vi.fn(async () => ({ csrfToken: "csrf-token", user: { id: 5, role: "ADMIN" } })) },
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
    renderPage();

    expect(screen.getByText(/secure, single use invitation token/)).toBeTruthy();
    expect(screen.queryByText(/signed invitation/)).toBeNull();
    expect(screen.getByLabelText(/^Invitation token/).value).toBe("invite-token");

    fireEvent.change(screen.getByLabelText("Username"), { target: { value: "new_admin" } });
    fireEvent.change(screen.getByLabelText("Email (must match invitation)"), { target: { value: "admin@example.invalid" } });
    fireEvent.change(screen.getByLabelText("First name"), { target: { value: "New" } });
    fireEvent.change(screen.getByLabelText("Last name"), { target: { value: "Admin" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "AdminPass123" } });
    fireEvent.change(screen.getByLabelText("Confirm password"), { target: { value: "AdminPass123" } });
    fireEvent.click(screen.getByRole("button", { name: "Create administrator account" }));

    await waitFor(() => expect(screen.getByText("Admin home after redemption")).toBeTruthy());
    expect(mocks.api.post).toHaveBeenCalledWith(
      "/auth/admin-invitations/accept/",
      expect.objectContaining({
        token: "invite-token",
        username: "new_admin",
        email: "admin@example.invalid",
      })
    );
    expect(mocks.signInWithData).toHaveBeenCalledWith({ csrfToken: "csrf-token", user: { id: 5, role: "ADMIN" } });
  });

  it("rejects mismatched passwords before calling the API", async () => {
    renderPage();

    fireEvent.change(screen.getByLabelText("Username"), { target: { value: "new_admin" } });
    fireEvent.change(screen.getByLabelText("Email (must match invitation)"), { target: { value: "admin@example.invalid" } });
    fireEvent.change(screen.getByLabelText("First name"), { target: { value: "New" } });
    fireEvent.change(screen.getByLabelText("Last name"), { target: { value: "Admin" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "AdminPass123" } });
    fireEvent.change(screen.getByLabelText("Confirm password"), { target: { value: "Different123" } });
    fireEvent.click(screen.getByRole("button", { name: "Create administrator account" }));

    expect(await screen.findByText("Passwords do not match.")).toBeTruthy();
    expect(mocks.api.post).not.toHaveBeenCalled();
  });
});
