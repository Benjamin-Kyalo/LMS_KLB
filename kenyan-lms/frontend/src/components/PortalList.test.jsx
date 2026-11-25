import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import PortalList from "./PortalList";

vi.mock("../hooks/useApi", () => ({
  useList: () => ({
    data: [{ id: 1, title: "Introduction to Fractions", resource_type: "PDF", offline_available: true }],
    loading: false,
    error: null,
    reload: vi.fn(),
  }),
}));

const columns = [
  { key: "title", label: "Resource" },
  { key: "resource_type", label: "Type" },
  { key: "offline_available", label: "Downloadable", render: (r) => (r.offline_available ? "Yes" : "No") },
];

describe("PortalList", () => {
  afterEach(cleanup);

  it("shows read-only rows with a detail view and no edit controls", async () => {
    const user = userEvent.setup();
    render(<PortalList title="Learning resources" overline="Portal" endpoint="/content/resources/" columns={columns} />);
    expect(screen.getByText("Introduction to Fractions")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Edit" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Delete" })).toBeNull();
    await user.click(screen.getByRole("button", { name: "View Introduction to Fractions" }));
    expect(screen.getByRole("dialog", { name: /Learning resources details/i })).toBeTruthy();
  });
});
