import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import PortalSubmissions from "./PortalSubmissions";

const mocks = vi.hoisted(() => ({
  post: vi.fn(async () => ({})),
  upload: vi.fn(async () => ({})),
  reload: vi.fn(async () => {}),
  push: vi.fn(),
  actor: { id: 7, role: "LEARNER" },
  submissions: [{
    id: 9,
    learner_name: " learner ",
    assignment_title: "Essay",
    submitted_at: "2026-11-26T08:00:00Z",
    status: "RETURNED",
    score: "9.00",
    assignment_max_score: "10.00",
    feedback: "Good structure.",
    feedback_published_at: "2026-11-26T10:00:00Z",
    current_attempt: 1,
    allow_resubmission: true,
    max_attempts: 2,
    text_answer: "First answer",
    criterion_scores: [],
    attempts: [{ id: 91, attempt_number: 1, submitted_at: "2026-11-26T08:00:00Z" }],
  }],
}));

vi.mock("../context/AuthContext", () => ({ useAuth: () => ({ user: mocks.actor }) }));
vi.mock("../context/ToastContext", () => ({ useToast: () => ({ push: mocks.push }) }));
vi.mock("../services/api", () => ({
  api: { post: mocks.post, upload: mocks.upload },
}));
vi.mock("../hooks/useApi", () => ({
  useList: () => ({ data: mocks.submissions, loading: false, error: null, reload: mocks.reload }),
}));

describe("portal submission feedback", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
    mocks.actor = { id: 7, role: "LEARNER" };
  });

  it("lets a learner send a new attempt", async () => {
    render(<PortalSubmissions />);
    fireEvent.click(screen.getByRole("button", { name: "Resubmit Essay" }));
    const dialog = screen.getByRole("dialog");
    fireEvent.change(within(dialog).getByLabelText("Answer"), { target: { value: "Improved answer" } });
    fireEvent.click(within(dialog).getByRole("button", { name: "Send new attempt" }));

    await waitFor(() => expect(mocks.post).toHaveBeenCalledWith(
      "/courses/submissions/9/resubmit/",
      { text_answer: "Improved answer" },
    ));
  });

  it("hides the resubmit action from guardians", () => {
    mocks.actor = { id: 8, role: "GUARDIAN" };
    render(<PortalSubmissions />);
    expect(screen.queryByRole("button", { name: "Resubmit Essay" })).toBeNull();
    expect(screen.getByRole("button", { name: "View feedback for Essay" })).toBeTruthy();
  });

  it("shows published feedback and criterion comments", () => {
    mocks.submissions = [{
      ...mocks.submissions[0],
      criterion_scores: [{
        id: 92, criterion_name: "Content", score: "4.00", max_score: "5.00", comment: "Clear point.",
      }],
    }];
    render(<PortalSubmissions />);
    fireEvent.click(screen.getByRole("button", { name: "View feedback for Essay" }));
    const dialog = screen.getByRole("dialog");
    expect(within(dialog).getByText("Good structure.")).toBeTruthy();
    expect(within(dialog).getByText("Clear point.")).toBeTruthy();
  });
});
