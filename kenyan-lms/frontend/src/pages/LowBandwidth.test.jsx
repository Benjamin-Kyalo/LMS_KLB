import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import LowBandwidth from "./LowBandwidth";

const mocks = vi.hoisted(() => ({
  push: vi.fn(),
  dismissConflict: vi.fn(),
  clearCache: vi.fn(),
  clearConflicts: vi.fn(),
  flush: vi.fn(async () => ({ sent: 1, conflicts: 0, kept: 0 })),
}));

vi.mock("../context/LowBandwidthContext", () => ({
  useLowBandwidth: () => ({
    config: { offline: { enabled: true } },
    online: true,
    revision: 1,
    status: { cached_reads: 2, queued_writes: 1, conflicts: 1 },
    flush: mocks.flush,
  }),
}));
vi.mock("../context/ToastContext", () => ({ useToast: () => ({ push: mocks.push }) }));
vi.mock("../services/lowBandwidth", () => ({
  clearCache: mocks.clearCache,
  clearConflicts: mocks.clearConflicts,
  dismissConflict: mocks.dismissConflict,
  listConflicts: () => [{
    id: "c1", method: "PATCH", path: "/theming/site-content/",
    message: "This record changed since you loaded it.",
    server_updated_at: "2026-11-26T11:00:00+00:00",
  }],
  listOutbox: () => [{
    id: "o1", method: "PATCH", path: "/theming/site-content/",
    created_at: "2026-11-26T10:00:00+00:00", if_match: "2026-11-26T10:00:00+00:00",
  }],
}));

describe("low-bandwidth status", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("shows connection, queue and privacy state", () => {
    render(<LowBandwidth />);
    expect(screen.getByRole("heading", { name: "Low-bandwidth status" })).toBeTruthy();
    expect(screen.getByText(/Connection: online/)).toBeTruthy();
    expect(screen.getAllByRole("cell", { name: "/theming/site-content/" }).length).toBeGreaterThan(0);
    expect(screen.getByText(/Session cookies, CSRF tokens and credentials are never saved/)).toBeTruthy();
  });

  it("retries queued changes with a visible busy label", async () => {
    render(<LowBandwidth />);
    fireEvent.click(screen.getByRole("button", { name: "Retry queued changes" }));
    await waitFor(() => expect(mocks.flush).toHaveBeenCalled());
    expect(mocks.push).toHaveBeenCalledWith(
      expect.stringContaining("Retried 1 queued change"), "success",
    );
  });
});
