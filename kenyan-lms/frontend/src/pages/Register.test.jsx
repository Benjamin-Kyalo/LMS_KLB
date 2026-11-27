import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Register from "./Register";

const mocks = vi.hoisted(() => ({
  api: { post: vi.fn(async () => ({ id: 9 })) },
  listAll: vi.fn(async () => [{ id: 3, name: "Mwangaza Demo School", code: "DEMO01" }]),
  signIn: vi.fn(async () => ({ user: { id: 9, role: "LEARNER", onboarding: { is_complete: true } } })),
}));

vi.mock("../services/api", () => ({ api: mocks.api, listAll: mocks.listAll }));
vi.mock("../context/AuthContext", () => ({ useAuth: () => ({ signIn: mocks.signIn }) }));

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/register"]}>
      <Routes>
        <Route path="/register" element={<Register />} />
        <Route path="/onboarding" element={<div>First-time setup</div>} />
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
    expect(screen.getByText(/Administrator accounts need a secure invitation/)).toBeTruthy();
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
    await user.type(screen.getByLabelText(/^Username/), "test_learner");
    await user.type(screen.getByLabelText("Email"), "test.learner@example.invalid");
    await user.type(screen.getByLabelText(/^Password/), "TestPass123");
    await user.type(screen.getByLabelText("Confirm password"), "TestPass123");
    await user.type(screen.getByLabelText("Date of birth"), "2012-05-04");
    await user.selectOptions(screen.getByLabelText("Gender"), "F");
    await user.selectOptions(screen.getByLabelText("School / institution"), "3");
    await user.click(screen.getByRole("button", { name: "Create account" }));

    await waitFor(() => expect(screen.getByText("Portal after sign-in")).toBeTruthy(), { timeout: 10000 });
    expect(mocks.api.post).toHaveBeenCalledWith(
      "/auth/register/",
      expect.objectContaining({ role: "LEARNER", username: "test_learner" })
    );
    expect(mocks.signIn).toHaveBeenCalledWith("test_learner", "TestPass123");
  }, 20000);

  it("asks guardians for a learner identifier and sends it in the registration payload", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole("radio", { name: /Parent \/ Guardian/ }));
    expect(screen.getByText(/Your school verifies this link before any learner data is shown/)).toBeTruthy();

    await user.type(screen.getByLabelText("First name"), "Mary");
    await user.type(screen.getByLabelText("Last name"), "Otieno");
    await user.type(screen.getByLabelText(/^Username/), "test_guardian");
    await user.type(screen.getByLabelText("Email"), "test.guardian@example.invalid");
    await user.type(screen.getByLabelText(/^Password/), "TestPass123");
    await user.type(screen.getByLabelText("Confirm password"), "TestPass123");
    await user.selectOptions(screen.getByLabelText("School / institution"), "3");
    await user.type(screen.getByLabelText("Relationship to learner"), "Parent");
    await user.type(screen.getByLabelText(/Learner admission or assessment number/), "ADM-100");
    await user.click(screen.getByRole("button", { name: "Create account" }));

    await waitFor(() => expect(mocks.api.post).toHaveBeenCalledWith(
      "/auth/register/",
      expect.objectContaining({ role: "GUARDIAN", learner_identifier: "ADM-100" }),
    ));
  }, 20000);

  it("sends incomplete accounts to first-time setup after registration", async () => {
    const user = userEvent.setup();
    mocks.signIn.mockResolvedValueOnce({
      user: { id: 10, role: "LEARNER", onboarding: { is_complete: false } },
    });
    renderPage();

    await user.type(screen.getByLabelText("First name"), "New");
    await user.type(screen.getByLabelText("Last name"), "Learner");
    await user.type(screen.getByLabelText(/^Username/), "setup_learner");
    await user.type(screen.getByLabelText("Email"), "setup@example.invalid");
    await user.type(screen.getByLabelText(/^Password/), "TestPass123");
    await user.type(screen.getByLabelText("Confirm password"), "TestPass123");
    await user.type(screen.getByLabelText("Date of birth"), "2012-05-04");
    await user.selectOptions(screen.getByLabelText("Gender"), "F");
    await user.selectOptions(screen.getByLabelText("School / institution"), "3");
    await user.click(screen.getByRole("button", { name: "Create account" }));

    await waitFor(() => expect(screen.getByText("First-time setup")).toBeTruthy());
  }, 20000);
});
