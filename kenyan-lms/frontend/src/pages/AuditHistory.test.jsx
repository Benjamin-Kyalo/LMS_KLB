import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AuditHistory from "./AuditHistory";

const mocks = vi.hoisted(() => ({
  reload: vi.fn(),
  entries: [
    {
      id: 5, actor_name: "Mary Admin", actor_username: "mary_admin", action: "learner.updated",
      entity_type: "Learner", entity_id: 4, created_at: "2026-11-26T09:00:00Z",
      ip_address: "127.0.0.1",
      details: {
        changed_fields: ["first_name"],
        before: { first_name: "Amina" }, after: { first_name: "Faith" },
      },
    },
    {
      id: 4, actor_name: "Peter Admin", actor_username: "peter_admin", action: "link.verified",
      entity_type: "LearnerGuardian", entity_id: 9, created_at: "2026-11-25T09:00:00Z",
      ip_address: "", details: { guardian: "Mary Wambui" },
    },
  ],
}));

vi.mock("../hooks/useApi", () => ({
  useList: () => ({ data: mocks.entries, loading: false, error: null, reload: mocks.reload }),
}));

function renderPage() {
  return render(<AuditHistory />);
}

describe("audit history", () => {
  afterEach(() => {
    cleanup();
    mocks.reload.mockClear();
  });

  it("shows field-level before and after values for an entry", async () => {
    const user = userEvent.setup();
    renderPage();

    expect(screen.getByText("Mary Admin")).toBeTruthy();
    await user.click(screen.getByRole("button", { name: "View audit entry 5" }));

    const dialog = screen.getByRole("dialog");
    expect(within(dialog).getByText("Amina")).toBeTruthy();
    expect(within(dialog).getByText("Faith")).toBeTruthy();
    expect(within(dialog).getByText("first_name")).toBeTruthy();
  });

  it("filters the history by action", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.selectOptions(screen.getByLabelText("Action"), "link.verified");

    await waitFor(() => expect(screen.queryByText("Mary Admin")).toBeNull());
    expect(screen.getByText("Peter Admin")).toBeTruthy();
  });
});
