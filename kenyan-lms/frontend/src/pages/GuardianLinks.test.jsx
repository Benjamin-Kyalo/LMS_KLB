import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import GuardianLinks from "./GuardianLinks";

const mocks = vi.hoisted(() => ({
  api: { post: vi.fn(async () => ({})) },
  push: vi.fn(),
  reload: vi.fn(),
}));

vi.mock("../services/api", () => ({ api: mocks.api }));
vi.mock("../context/ToastContext", () => ({ useToast: () => ({ push: mocks.push }) }));
vi.mock("../hooks/useApi", () => ({
  useList: () => ({
    data: [{
      id: 4, guardian_name: "Mary Otieno", learner_name: "Faith Otieno",
      admission_number: "ADM-100", relationship: "Parent", status: "PENDING",
      created_at: "2026-11-24T09:00:00Z",
    }],
    loading: false,
    error: null,
    reload: mocks.reload,
  }),
}));

function renderPage() {
  return render(<MemoryRouter><GuardianLinks /></MemoryRouter>);
}

describe("guardian links", () => {
  afterEach(() => {
    cleanup();
    mocks.api.post.mockClear();
    mocks.push.mockClear();
    mocks.reload.mockClear();
  });

  it("verifies a link only through the explicit verification action", async () => {
    const user = userEvent.setup();
    renderPage();

    expect(screen.getByText("Mary Otieno")).toBeTruthy();
    expect(screen.getByText(/1 link request is awaiting verification/)).toBeTruthy();

    await user.click(screen.getByRole("button", { name: "Verify guardian link for Mary Otieno" }));
    await user.click(screen.getByRole("button", { name: "Verify link" }));

    await waitFor(() => expect(mocks.api.post).toHaveBeenCalledWith(
      "/learners/link-requests/4/verify/", expect.any(Object),
    ));
    expect(mocks.push).toHaveBeenCalledWith("Guardian link verified.", "success");
    expect(mocks.reload).toHaveBeenCalled();
  });

  it("requires a reason before rejecting a link", async () => {
    const user = userEvent.setup();
    renderPage();

    // The hold-confirm button also accepts Enter as its accessible fallback.
    const reject = screen.getByRole("button", { name: "Reject guardian link for Mary Otieno" });
    reject.focus();
    await user.keyboard("{Enter}");
    await user.click(screen.getByRole("button", { name: "Reject link" }));

    expect(mocks.api.post).not.toHaveBeenCalled();
    expect(screen.getByText(/Give a short reason/)).toBeTruthy();
  });
});
