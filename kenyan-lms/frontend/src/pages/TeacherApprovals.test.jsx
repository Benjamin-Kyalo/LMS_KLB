import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import TeacherApprovals from "./TeacherApprovals";

const mocks = vi.hoisted(() => ({
  api: { post: vi.fn(async () => ({})) },
  listAll: vi.fn(async () => []),
  push: vi.fn(),
  reload: vi.fn(),
}));

vi.mock("../services/api", () => ({ api: mocks.api, listAll: mocks.listAll }));
vi.mock("../context/ToastContext", () => ({ useToast: () => ({ push: mocks.push }) }));
vi.mock("../hooks/useApi", () => ({
  useList: () => ({
    data: [{
      id: 7, teacher_name: "Peter Kamau", email: "peter@example.invalid",
      employment_type: "CONTRACT", status: "PENDING", created_at: "2026-11-24T09:00:00Z",
    }],
    loading: false,
    error: null,
    reload: mocks.reload,
  }),
}));

function renderPage() {
  return render(<MemoryRouter><TeacherApprovals /></MemoryRouter>);
}

describe("teacher approvals", () => {
  afterEach(() => {
    cleanup();
    mocks.api.post.mockClear();
    mocks.push.mockClear();
    mocks.reload.mockClear();
  });

  it("shows pending accounts and approves them through the explicit action", async () => {
    const user = userEvent.setup();
    renderPage();

    expect(screen.getByText("Peter Kamau")).toBeTruthy();
    expect(screen.getByText(/1 teacher account is awaiting review/)).toBeTruthy();

    await user.click(screen.getByRole("button", { name: "Approve teacher account for Peter Kamau" }));
    expect(screen.getByRole("dialog", { name: "Approve teacher account" })).toBeTruthy();

    await user.click(screen.getByRole("button", { name: "Approve account" }));

    await waitFor(() => expect(mocks.api.post).toHaveBeenCalledWith(
      "/teachers/approvals/7/approve/", expect.any(Object),
    ));
    expect(mocks.push).toHaveBeenCalledWith("Teacher approved.", "success");
    expect(mocks.reload).toHaveBeenCalled();
  });

  it("requires a reason when rejecting and does not activate the account", async () => {
    const user = userEvent.setup();
    renderPage();

    // The hold-confirm button also accepts Enter as its accessible fallback.
    const reject = screen.getByRole("button", { name: "Reject teacher account for Peter Kamau" });
    reject.focus();
    await user.keyboard("{Enter}");
    expect(screen.getByRole("dialog", { name: "Reject teacher account" })).toBeTruthy();
    await user.click(screen.getByRole("button", { name: "Reject account" }));

    expect(mocks.api.post).not.toHaveBeenCalled();
    expect(screen.getByText(/Give a short reason/)).toBeTruthy();
  });
});
