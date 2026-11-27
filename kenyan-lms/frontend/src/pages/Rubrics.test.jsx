import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import Rubrics from "./Rubrics";

const mocks = vi.hoisted(() => ({
  post: vi.fn(async () => ({})),
  patch: vi.fn(async () => ({})),
  del: vi.fn(async () => ({})),
  reload: vi.fn(async () => {}),
  push: vi.fn(),
  rubrics: [{
    id: 1,
    name: "Essay rubric",
    institution_code: "SCH",
    description: "Writing assessment",
    levels: [{ id: 11 }],
    criteria: [{ id: 21 }],
  }],
  levels: [{
    id: 11, rubric: 1, name: "Beginning", min_score: "0", max_score: "40", sequence: 1,
  }],
  criteria: [{ id: 21, rubric: 1, name: "Content", max_score: "5", sequence: 1 }],
  comments: [{ id: 31, category: "Writing", text: "Clear thesis." }],
}));

vi.mock("../context/AuthContext", () => ({ useAuth: () => ({ user: { id: 1, role: "ADMIN" } }) }));
vi.mock("../context/ToastContext", () => ({ useToast: () => ({ push: mocks.push }) }));
vi.mock("../services/api", () => ({
  api: { post: mocks.post, patch: mocks.patch, del: mocks.del },
  listAll: vi.fn(async () => []),
}));
vi.mock("../hooks/useApi", () => ({
  useList: (path) => {
    if (path === "/curriculum/rubric-levels/") {
      return { data: mocks.levels, loading: false, error: null, reload: mocks.reload };
    }
    if (path === "/curriculum/rubric-criteria/") {
      return { data: mocks.criteria, loading: false, error: null, reload: mocks.reload };
    }
    if (path === "/curriculum/feedback-comments/") {
      return { data: mocks.comments, loading: false, error: null, reload: mocks.reload };
    }
    return { data: mocks.rubrics, loading: false, error: null, reload: mocks.reload };
  },
}));

describe("rubric builder", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("shows the rubric with its bands, criteria and comment bank", () => {
    render(<Rubrics />);
    expect(screen.getByRole("heading", { name: "Rubrics & feedback" })).toBeTruthy();
    expect(screen.getByRole("cell", { name: "Essay rubric" })).toBeTruthy();
    expect(screen.getByRole("cell", { name: "Beginning" })).toBeTruthy();
    expect(screen.getByRole("cell", { name: "Content" })).toBeTruthy();
    expect(screen.getByRole("cell", { name: "Clear thesis." })).toBeTruthy();
  });

  it("creates a criterion on the selected rubric", async () => {
    render(<Rubrics />);
    fireEvent.click(screen.getByRole("button", { name: "New criterion" }));
    const dialog = screen.getByRole("dialog");
    fireEvent.change(within(dialog).getByLabelText("Criterion name"), { target: { value: "Evidence" } });
    fireEvent.change(within(dialog).getByLabelText("Maximum score"), { target: { value: "5" } });
    fireEvent.click(within(dialog).getByRole("button", { name: "Create criterion" }));

    await waitFor(() => expect(mocks.post).toHaveBeenCalledWith(
      "/curriculum/rubric-criteria/",
      expect.objectContaining({ rubric: 1, name: "Evidence", max_score: 5 }),
    ));
    expect(mocks.reload).toHaveBeenCalled();
  });

  it("rejects overlapping achievement bands before saving", async () => {
    render(<Rubrics />);
    fireEvent.click(screen.getByRole("button", { name: "New band" }));
    const dialog = screen.getByRole("dialog");
    fireEvent.change(within(dialog).getByLabelText("Band name"), { target: { value: "Wrong" } });
    fireEvent.change(within(dialog).getByLabelText("Minimum percentage"), { target: { value: "80" } });
    fireEvent.change(within(dialog).getByLabelText("Maximum percentage"), { target: { value: "40" } });
    fireEvent.click(within(dialog).getByRole("button", { name: "Create achievement band" }));

    expect(within(dialog).getByRole("alert").textContent).toMatch(/minimum cannot be higher/i);
    expect(mocks.post).not.toHaveBeenCalled();
  });

  it("deletes a band from a normal confirmation button", async () => {
    render(<Rubrics />);
    fireEvent.click(screen.getByRole("button", { name: "Delete band Beginning" }));
    const dialog = screen.getByRole("dialog");
    fireEvent.click(within(dialog).getByRole("button", { name: "Delete achievement band" }));

    await waitFor(() => expect(mocks.del).toHaveBeenCalledWith("/curriculum/rubric-levels/11/"));
  });
});
