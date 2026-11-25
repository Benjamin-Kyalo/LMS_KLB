import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import Onboarding from "./Onboarding";

const mocks = vi.hoisted(() => ({
  api: {
    post: vi.fn(async () => ({})),
    patch: vi.fn(async () => ({})),
    get: vi.fn(async () => ({ id: 2, role: "GUARDIAN", onboarding: { is_complete: false } })),
  },
  reloadList: vi.fn(),
  reloadChecklist: vi.fn(),
  setUser: vi.fn(),
}));

vi.mock("../services/api", () => ({ api: mocks.api }));
vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({
    user: { id: 2, username: "amina", first_name: "Amina", role: "GUARDIAN" },
    setUser: mocks.setUser,
  }),
}));
vi.mock("../hooks/useApi", () => ({
  useList: () => ({ data: [], loading: false, error: null, reload: mocks.reloadList }),
  useResource: () => ({
    data: {
      is_complete: false,
      profile_complete: false,
      steps: [
        { key: "profile_complete", label: "Confirm your profile details", done: false },
        { key: "guardian_link_verified", label: "Your learner link is verified", done: false },
      ],
    },
    loading: false,
    error: null,
    reload: mocks.reloadChecklist,
  }),
}));

function renderPage() {
  return render(<MemoryRouter><Onboarding /></MemoryRouter>);
}

describe("first-time setup", () => {
  afterEach(() => {
    cleanup();
    mocks.api.post.mockClear();
    mocks.api.patch.mockClear();
    mocks.reloadList.mockClear();
    mocks.reloadChecklist.mockClear();
    mocks.setUser.mockClear();
  });

  it("shows the role-specific checklist and a learner link form for guardians", () => {
    renderPage();
    expect(screen.getByRole("heading", { name: /Welcome, Amina/ })).toBeTruthy();
    expect(screen.getByText("Your learner link is verified")).toBeTruthy();
    expect(screen.getByLabelText("Learner admission or assessment number")).toBeTruthy();
  });

  it("submits a learner identifier through the guarded link endpoint", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.type(screen.getByLabelText("Learner admission or assessment number"), "ADM-100");
    await user.click(screen.getByRole("button", { name: "Submit learner link" }));

    await waitFor(() => expect(mocks.api.post).toHaveBeenCalledWith(
      "/learners/link-requests/",
      expect.objectContaining({ learner_identifier: "ADM-100" }),
    ));
    expect(mocks.reloadList).toHaveBeenCalled();
  });

  it("only lets the account owner confirm their own profile details", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole("button", { name: "Confirm my details" }));

    await waitFor(() => expect(mocks.api.patch).toHaveBeenCalledWith(
      "/auth/onboarding/me/", { profile_complete: true },
    ));
    expect(mocks.setUser).toHaveBeenCalled();
    expect(mocks.reloadChecklist).toHaveBeenCalled();
  });
});
