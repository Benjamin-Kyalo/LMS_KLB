import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Register from "./Register";

const mocks = vi.hoisted(() => ({
  api: { post: vi.fn(async () => ({ id: 9 })) },
  listAll: vi.fn(async () => [{ id: 3, name: "Mwangaza Demo School", code: "DEMO01" }]),
  signIn: vi.fn(async () => ({ user: { id: 9, role: "LEARNER" } })),
}));

vi.mock("../services/api", () => ({ api: mocks.api, listAll: mocks.listAll }));
vi.mock("../context/AuthContext", () => ({ useAuth: () => ({ signIn: mocks.signIn }) }));

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/register"]}>
      <Routes>
        <Route path="/register" element={<Register />} />
        <Route path="/portal" element={<div>Portal after sign-in</div>} />
      </Routes>
    </MemoryRouter>
  );
}

describe("public registration", () => {
  afterEach(() => {
    cleanup();
    mocks.api.post.mockClear();
    mocks.signIn.mockClear();
  });

  it("offers only public roles and changes fields with the selected role", async () => {
    const user = userEvent.setup();
    const { container } = renderPage();

    expect(screen.queryByRole("radio", { name: /administrator/i })).toBeNull();
    expect([...container.querySelectorAll("a")].some((link) => (link.getAttribute("href") || "").includes("/admin"))).toBe(false);
    expect(screen.getByText(/secure, single-use invitation token/)).toBeTruthy();
    expect(screen.getByLabelText("Date of birth")).toBeTruthy();

    await user.click(screen.getByRole("radio", { name: /Teacher/ }));
    expect(screen.getByLabelText("Employment type")).toBeTruthy();
    expect(screen.queryByLabelText("Date of birth")).toBeNull();

    await user.click(screen.getByRole("radio", { name: /Parent \/ Guardian/ }));
    expect(screen.getByLabelText("Relationship to learner")).toBeTruthy();
    expect(screen.queryByLabelText("Employment type")).toBeNull();
  });

  it("creates a learner account and signs the user into the portal", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.type(screen.getByLabelText("First name"), "Test");
    await user.type(screen.getByLabelText("Last name"), "Learner");
    await user.type(screen.getByLabelText("Username"), "test_learner");
    await user.type(screen.getByLabelText("Email"), "test.learner@example.invalid");
    await user.type(screen.getByLabelText(/^Password/), "TestPass123");
    await user.type(screen.getByLabelText("Confirm password"), "TestPass123");
    await user.type(screen.getByLabelText("Date of birth"), "2012-05-04");
    await user.selectOptions(screen.getByLabelText("Gender"), "F");
    await user.selectOptions(screen.getByLabelText("School / institution"), "3");
    await user.click(screen.getByRole("button", { name: "Create account" }));

    await waitFor(() => expect(screen.getByText("Portal after sign-in")).toBeTruthy());
    expect(mocks.api.post).toHaveBeenCalledWith(
      "/auth/register/",
      expect.objectContaining({ role: "LEARNER", username: "test_learner" })
    );
    expect(mocks.signIn).toHaveBeenCalledWith("test_learner", "TestPass123");
  });
});
