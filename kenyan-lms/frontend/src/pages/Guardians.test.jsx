import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Guardians from "./Guardians";

const mocks = vi.hoisted(() => ({
  guardian: {
    id: 12,
    guardian_name: "Mary Wambui",
    username: "mary_wambui",
    guardian_number: "GD_MDSCH_2026/11_001",
    learner_names: [],
  },
  learner: {
    id: 4,
    learner_name: "Benjamin Kyalo",
    username: "benjamin_kyalo",
    admission_number: "LR_MDSCH_2026/11_001",
    class_name: "Grade 4 A",
    guardian_names: [],
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
    data: path === "/guardians/" ? [mocks.guardian] : [],
    loading: false,
    error: null,
    reload: vi.fn(),
  }),
}));

import { api } from "../services/api";

describe("Guardians learner linking", () => {
  beforeEach(() => {
    api.get.mockReset();
    api.post.mockReset();
    api.post.mockResolvedValue({});
    api.get.mockImplementation((path) => path.startsWith("/learners/?search")
      ? Promise.resolve({ results: [mocks.learner] })
      : Promise.resolve({ results: [] }));
  });

  afterEach(() => cleanup());

  it("searches live and posts the selected learner id with access permissions", async () => {
    const user = userEvent.setup();
    render(<Guardians />);

    await user.click(screen.getByRole("button", { name: "Link learner" }));
    const dialog = screen.getByRole("dialog");
    await user.type(
      within(dialog).getByPlaceholderText("Type a name, username or admission number"),
      "benj",
    );
    await waitFor(() => expect(api.get).toHaveBeenCalledWith("/learners/?search=benj"));
    await user.click(await within(dialog).findByText("Benjamin Kyalo"));

    expect(within(dialog).getByText("Selected learner")).toBeTruthy();
    expect(within(dialog).getByText("LR_MDSCH_2026/11_001")).toBeTruthy();

    await user.click(within(dialog).getByRole("checkbox", { name: /Fee information/ }));
    await user.click(within(dialog).getByRole("button", { name: "Link learner" }));

    expect(api.post).toHaveBeenCalledWith("/learners/guardian-links/", {
      learner: mocks.learner.id,
      guardian: mocks.guardian.id,
      relationship: "Parent",
      is_primary: true,
      can_view_academics: true,
      can_view_attendance: true,
      can_view_fees: true,
    });
  });
});
