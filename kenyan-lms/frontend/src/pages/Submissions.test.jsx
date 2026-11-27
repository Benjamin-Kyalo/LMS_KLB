import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import Submissions from "./Submissions";

const mocks = vi.hoisted(() => ({
  post: vi.fn(async () => ({})),
  get: vi.fn(async () => ({ id: 3, name: "Essay rubric" })),
  reload: vi.fn(async () => {}),
  push: vi.fn(),
  submissions: [{
    id: 5,
    learner_name: "Amina Yusuf",
    admission_number: "L-5",
    assignment_title: "Essay",
    submitted_at: "2026-11-26T08:00:00Z",
    status: "SUBMITTED",
    score: null,
    rubric: 3,
    rubric_name: "Essay rubric",
    assignment_max_score: "10.00",
    current_attempt: 1,
    graded_at: null,
    feedback_published_at: null,
    criterion_scores: [],
    attempts: [],
  }],
}));

vi.mock("../context/AuthContext", () => ({ useAuth: () => ({ user: { id: 1, role: "ADMIN" } }) }));
vi.mock("../context/ToastContext", () => ({ useToast: () => ({ push: mocks.push }) }));
vi.mock("../services/api", () => ({
  api: { post: mocks.post, get: mocks.get },
  listAll: vi.fn(async (path) => {
    if (path.includes("rubric-criteria")) return [
      { id: 21, name: "Content", max_score: "5.00" },
      { id: 22, name: "Language", max_score: "5.00" },
    ];
    return [];
  }),
}));
vi.mock("../hooks/useApi", () => ({
  useList: () => ({ data: mocks.submissions, loading: false, error: null, reload: mocks.reload }),
}));

describe("teacher submission workflow", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("grades every rubric criterion and saves the total server-side", async () => {
    render(<Submissions />);
    fireEvent.click(screen.getByRole("button", { name: "Grade submission from Amina Yusuf" }));
    const dialog = await screen.findByRole("dialog");
    fireEvent.change(within(dialog).getByLabelText("Score for Content"), { target: { value: "4" } });
    fireEvent.change(within(dialog).getByLabelText("Score for Language"), { target: { value: "5" } });
    fireEvent.click(within(dialog).getByRole("button", { name: "Save grade" }));

    await waitFor(() => expect(mocks.post).toHaveBeenCalledWith(
      "/courses/submissions/5/grade-rubric/",
      expect.objectContaining({
        criteria: [
          expect.objectContaining({ criterion: 21, score: "4" }),
          expect.objectContaining({ criterion: 22, score: "5" }),
        ],
      }),
    ));
    expect(mocks.reload).toHaveBeenCalled();
  });

  it("publishes feedback only after a normal confirmation click", async () => {
    mocks.submissions = [{
      ...mocks.submissions[0], status: "GRADED", score: "9.00",
      graded_at: "2026-11-26T09:00:00Z",
    }];
    render(<Submissions />);
    fireEvent.click(screen.getByRole("button", { name: "Publish feedback for Amina Yusuf" }));
    const dialog = screen.getByRole("dialog");
    expect(within(dialog).getByText(/private staff notes remain hidden/i)).toBeTruthy();
    fireEvent.click(within(dialog).getByRole("button", { name: "Publish feedback" }));

    await waitFor(() => expect(mocks.post).toHaveBeenCalledWith(
      "/courses/submissions/5/publish-feedback/",
    ));
  });
});
