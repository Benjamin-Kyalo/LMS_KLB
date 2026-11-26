import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Learners from "./Learners";

const mocks = vi.hoisted(() => ({
  learner: {
    id: 4, learner_name: "Benjamin Kyalo", username: "benjamin_kyalo",
    admission_number: "LR_MDSCH_2026/11_001", guardian_names: [], guardian_ids: [],
  },
  guardian: {
    id: 12, guardian_name: "Mary Wambui", username: "mary_wambui",
    guardian_number: "GD_MDSCH_2026/11_001", phone: "0700000001",
    email: "mary@example.com", relationship_to_learner: "Mother",
  },
  otherGuardian: {
    id: 13, guardian_name: "Peter Kiptoo", username: "peter_kiptoo",
    guardian_number: "GD_MDSCH_2026/11_002", phone: "0700000002",
    email: "peter@example.com", relationship_to_learner: "Father",
    learner_names: ["David Omondi"],
  },
}));

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({
    user: { id: 1, role: "ADMIN", capabilities: [], institution_id: 7 },
  }),
}));
vi.mock("../context/ToastContext", () => ({
  useToast: () => ({ push: vi.fn() }),
}));
vi.mock("../services/api", () => ({
  api: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), del: vi.fn() },
}));
vi.mock("../hooks/useApi", () => ({
  useList: (path) => ({
    data: path === "/learners/" ? [mocks.learner] : [],
    loading: false,
    error: null,
    reload: vi.fn(),
  }),
}));

import { api } from "../services/api";

async function typeAndChoose(dialog, user, name, searchTerm) {
  await user.type(
    within(dialog).getByPlaceholderText("Type a name, username, guardian number or phone"),
    searchTerm,
  );
  await waitFor(() => expect(api.get).toHaveBeenCalledWith(`/guardians/?search=${searchTerm}`));
  await user.click(await within(dialog).findByText(name));
}

async function chooseGuardian(dialog, user, name, searchTerm) {
  const people = name === "Mary Wambui" ? mocks.guardian : mocks.otherGuardian;
  api.get.mockImplementation((path) => {
    if (path.startsWith("/guardians/")) return Promise.resolve({ results: [people] });
    return Promise.resolve({ results: [] }); // no pending link request
  });
  await typeAndChoose(dialog, user, name, searchTerm);
}

describe("Learners guardian linking", () => {
  beforeEach(() => {
    mocks.learner.guardian_names = [];
    mocks.learner.guardian_ids = [];
    api.get.mockReset();
    api.post.mockReset();
    api.post.mockResolvedValue({});
  });

  afterEach(() => cleanup());

  it("searches live, prefills the guardian details and posts the selected id", async () => {
    const user = userEvent.setup();
    render(<Learners />);

    await user.click(screen.getByRole("button", { name: "Link guardian" }));
    const dialog = screen.getByRole("dialog");
    await chooseGuardian(dialog, user, "Mary Wambui", "mary");

    expect(within(dialog).getByText("Selected guardian")).toBeTruthy();
    expect(within(dialog).getByText("GD_MDSCH_2026/11_001")).toBeTruthy();
    expect(within(dialog).getByDisplayValue("Mother")).toBeTruthy();

    await user.click(within(dialog).getByRole("checkbox", { name: /Fee information/ }));
    await user.click(within(dialog).getByRole("button", { name: "Link guardian" }));
    expect(api.post).toHaveBeenCalledWith("/learners/guardian-links/", {
      learner: mocks.learner.id,
      guardian: mocks.guardian.id,
      relationship: "Mother",
      is_primary: true,
      can_view_academics: true,
      can_view_attendance: true,
      can_view_fees: true,
    });
  });

  it("shows existing links and requires confirmation before adding another guardian", async () => {
    mocks.learner.guardian_names = ["Mary Wambui"];
    mocks.learner.guardian_ids = [mocks.guardian.id];
    const user = userEvent.setup();
    render(<Learners />);

    await user.click(screen.getByRole("button", { name: "Add guardian" }));
    const dialog = screen.getByRole("dialog");
    await chooseGuardian(dialog, user, "Peter Kiptoo", "peter");

    expect(within(dialog).getAllByText(/already linked to/).length).toBeGreaterThan(0);
    expect(within(dialog).getByText("David Omondi")).toBeTruthy();
    const submit = within(dialog).getByRole("button", { name: "Link guardian" });
    expect(submit.disabled).toBe(true);

    await user.click(within(dialog).getByRole("checkbox", { name: /I have reviewed/ }));
    expect(submit.disabled).toBe(false);
    await user.click(submit);
    expect(api.post).toHaveBeenCalledWith("/learners/guardian-links/", {
      learner: mocks.learner.id,
      guardian: mocks.otherGuardian.id,
      relationship: "Father",
      is_primary: true,
      can_view_academics: true,
      can_view_attendance: true,
      can_view_fees: false,
    });
  });

  it("lets the admin verify a pending request inline", async () => {
    const user = userEvent.setup();
    render(<Learners />);
    api.get.mockImplementation((path) => path.startsWith("/guardians/")
      ? Promise.resolve({ results: [mocks.guardian] })
      : Promise.resolve({ results: [{
          id: 9, reference: "GL-1", guardian: mocks.guardian.id,
          learner: mocks.learner.id, status: "PENDING",
        }] }));

    await user.click(screen.getByRole("button", { name: "Link guardian" }));
    const dialog = screen.getByRole("dialog");
    await typeAndChoose(dialog, user, "Mary Wambui", "mary");

    expect(await within(dialog).findByText(/waiting for verification/)).toBeTruthy();
    expect(within(dialog).getByRole("button", { name: "Link guardian" }).disabled).toBe(true);

    await user.click(within(dialog).getByRole("button", { name: "Verify link request GL-1" }));
    await user.click(within(dialog).getByRole("button", { name: "Verify link" }));

    expect(api.post).toHaveBeenCalledWith("/learners/link-requests/9/verify/", {
      notes: "",
      relationship: "Mother",
      is_primary: true,
      can_view_academics: true,
      can_view_attendance: true,
      can_view_fees: false,
    });
    expect(api.post).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
  });

  it("requires a reason before rejecting a pending request inline", async () => {
    const user = userEvent.setup();
    render(<Learners />);
    api.get.mockImplementation((path) => path.startsWith("/guardians/")
      ? Promise.resolve({ results: [mocks.guardian] })
      : Promise.resolve({ results: [{
          id: 9, reference: "GL-1", guardian: mocks.guardian.id,
          learner: mocks.learner.id, status: "PENDING",
        }] }));

    await user.click(screen.getByRole("button", { name: "Link guardian" }));
    const dialog = screen.getByRole("dialog");
    await typeAndChoose(dialog, user, "Mary Wambui", "mary");
    await user.click(await within(dialog).findByRole("button", { name: "Reject link request GL-1" }));

    await user.click(within(dialog).getByRole("button", { name: "Reject link" }));
    expect(within(dialog).getByRole("alert").textContent).toContain("Give a short reason");
    expect(api.post).not.toHaveBeenCalled();

    await user.type(within(dialog).getByLabelText(/Decision notes/), "Admission number does not match.");
    await user.click(within(dialog).getByRole("button", { name: "Reject link" }));
    expect(api.post).toHaveBeenCalledWith("/learners/link-requests/9/reject/", {
      notes: "Admission number does not match.",
      relationship: "Mother",
      is_primary: true,
      can_view_academics: true,
      can_view_attendance: true,
      can_view_fees: false,
    });
    expect(api.post).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
  });

  it("blocks a duplicate link and explains why", async () => {
    mocks.learner.guardian_names = ["Mary Wambui"];
    mocks.learner.guardian_ids = [mocks.guardian.id];
    const user = userEvent.setup();
    render(<Learners />);

    await user.click(screen.getByRole("button", { name: "Add guardian" }));
    const dialog = screen.getByRole("dialog");
    await chooseGuardian(dialog, user, "Mary Wambui", "mary");

    expect(within(dialog).getByRole("alert").textContent).toContain("already linked to that learner");
    expect(within(dialog).getByRole("button", { name: "Link guardian" }).disabled).toBe(true);
    expect(api.post).not.toHaveBeenCalled();
  });
});
