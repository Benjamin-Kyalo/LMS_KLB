import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import EarlyWarning from "./EarlyWarning";

const mocks = vi.hoisted(() => ({
  api: { post: vi.fn(async () => ({ tasks_created: 1 })) },
  push: vi.fn(),
  reloadReport: vi.fn(),
  reloadTasks: vi.fn(),
  report: {
    rules: {
      ATTENDANCE: {
        label: "Low attendance",
        description: "Above 20% absent over 30 days with at least 5 marked days.",
      },
    },
    summary: { high: 1, medium: 0, low: 0, learners_checked: 12, total: 1 },
    alerts: [{
      learner_name: "Faith Otieno", admission_number: "ADM-100", class_name: "Grade 4 A",
      risk_score: 3, risk_level: "MEDIUM", open_task_count: 0,
      recommended_action: "Check the attendance register.",
      signals: [{
        code: "ATTENDANCE", label: "Low attendance", points: 3,
        detail: "3 of 10 days absent in the last 30 days (30%, threshold 20%).",
      }],
    }],
  },
  task: {
    id: 3, learner_name: "Faith Otieno", risk_level: "MEDIUM", status: "OPEN",
    assigned_to_name: "", due_date: "2026-12-03",
  },
}));

vi.mock("../services/api", () => ({ api: mocks.api }));
vi.mock("../context/ToastContext", () => ({ useToast: () => ({ push: mocks.push }) }));
vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({ user: { id: 7, role: "ADMIN" } }),
}));
vi.mock("../hooks/useApi", () => ({
  useResource: () => ({
    data: mocks.report, loading: false, error: null, reload: mocks.reloadReport,
  }),
  useList: () => ({
    data: [mocks.task], loading: false, error: null, reload: mocks.reloadTasks,
  }),
}));

function renderPage() {
  return render(<EarlyWarning />);
}

describe("early warning dashboard", () => {
  afterEach(() => {
    cleanup();
    mocks.api.post.mockClear();
    mocks.push.mockClear();
    mocks.reloadReport.mockClear();
    mocks.reloadTasks.mockClear();
  });

  it("shows the exact evidence behind a flag", async () => {
    const user = userEvent.setup();
    renderPage();

    expect(screen.getByText(/Above 20% absent over 30 days/)).toBeTruthy();
    await user.click(screen.getByRole("button", { name: "View evidence for Faith Otieno" }));

    const dialog = screen.getByRole("dialog");
    expect(within(dialog).getByText(/3 of 10 days absent/)).toBeTruthy();
    expect(within(dialog).getByText("Check the attendance register.")).toBeTruthy();
  });

  it("assigns a task to the signed-in staff member", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole("button", { name: "Assign Faith Otieno to me" }));

    await waitFor(() => expect(mocks.api.post).toHaveBeenCalledWith(
      "/analytics/interventions/3/assign/", { user_id: 7 },
    ));
    expect(mocks.push).toHaveBeenCalledWith("Task assigned to you.", "success");
    expect(mocks.reloadTasks).toHaveBeenCalled();
  });

  it("recalculates rules from the explicit refresh action", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole("button", { name: "Recalculate warnings" }));

    await waitFor(() => expect(mocks.api.post).toHaveBeenCalledWith(
      "/analytics/early-warning/refresh/", {},
    ));
    expect(mocks.reloadReport).toHaveBeenCalled();
  });
});
