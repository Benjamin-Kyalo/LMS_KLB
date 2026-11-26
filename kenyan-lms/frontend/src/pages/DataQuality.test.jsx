import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import DataQuality from "./DataQuality";

const mocks = vi.hoisted(() => ({
  api: { post: vi.fn() },
  push: vi.fn(),
  reload: vi.fn(),
  scan: {
    institution_id: 7, institution_name: "Quality School", total: 2,
    issues: [
      {
        code: "identifier_whitespace", label: "Identifiers with surrounding spaces",
        severity: "warning", count: 1, samples: ["Learner.admission_number #4"],
        fixable: true, detail: "Remove leading and trailing spaces from identifier fields.",
      },
      {
        code: "duplicate_admission_number", label: "Duplicate admission numbers",
        severity: "error", count: 0, samples: [], fixable: false,
        detail: "Each learner in a school needs a unique admission number.",
      },
    ],
  },
}));

vi.mock("../services/api", () => ({ api: mocks.api }));
vi.mock("../context/ToastContext", () => ({ useToast: () => ({ push: mocks.push }) }));
vi.mock("../hooks/useApi", () => ({
  useResource: () => ({ data: mocks.scan, loading: false, error: null, reload: mocks.reload }),
}));

function renderPage() {
  return render(<DataQuality />);
}

describe("data quality console", () => {
  afterEach(() => {
    cleanup();
    mocks.api.post.mockReset();
    mocks.push.mockClear();
    mocks.reload.mockClear();
  });

  it("previews changes and applies an allowlisted fix only after confirmation", async () => {
    const user = userEvent.setup();
    mocks.api.post
      .mockResolvedValueOnce({
        code: "identifier_whitespace", description: "Trim identifiers.",
        change_count: 1, applied: false,
        changes: [{
          entity_type: "Learner", entity_id: 4, field: "admission_number",
          before: "  qual-001  ", after: "qual-001",
        }],
      })
      .mockResolvedValueOnce({
        code: "identifier_whitespace", description: "Trim identifiers.",
        change_count: 1, applied: true,
        changes: [],
      });
    renderPage();

    expect(screen.queryByRole("button", { name: "Preview fix for Duplicate admission numbers" })).toBeNull();
    await user.click(screen.getByRole("button", { name: "Preview fix for Identifiers with surrounding spaces" }));

    const dialog = screen.getByRole("dialog");
    expect(within(dialog).getByText(
      (_, element) => element?.tagName === "TD" && element.textContent === "  qual-001  ",
    )).toBeTruthy();
    expect(within(dialog).getByText(
      (_, element) => element?.tagName === "TD" && element.textContent === "qual-001",
    )).toBeTruthy();

    within(dialog).getByRole("button", { name: /Apply 1 fix/ }).focus();
    await user.keyboard("{Enter}");

    await waitFor(() => expect(mocks.api.post).toHaveBeenCalledTimes(2));
    expect(mocks.api.post).toHaveBeenLastCalledWith("/core/data-quality/fix/", {
      issue_type: "identifier_whitespace", confirm: true,
    });
    expect(mocks.push).toHaveBeenCalledWith("1 record(s) updated and audited.", "success");
    expect(mocks.reload).toHaveBeenCalled();
  });
});
