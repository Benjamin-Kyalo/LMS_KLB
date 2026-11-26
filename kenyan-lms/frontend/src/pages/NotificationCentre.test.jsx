import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import NotificationCentre from "./NotificationCentre";

const mocks = vi.hoisted(() => ({
  api: { post: vi.fn(async () => ({})), patch: vi.fn(async () => ({})) },
  push: vi.fn(),
  reloadNotifications: vi.fn(),
  reloadUnread: vi.fn(),
  reloadPreferences: vi.fn(),
  notification: {
    id: 1, title: "Welcome", body: "A test alert", notification_type: "SYSTEM",
    link: "", is_read: false, created_at: "2026-11-26T09:00:00Z",
  },
  preference: { id: 9, in_app: true, email: true, sms: false, types: ["SYSTEM"] },
}));

vi.mock("../services/api", () => ({ api: mocks.api }));
vi.mock("../context/ToastContext", () => ({ useToast: () => ({ push: mocks.push }) }));
vi.mock("../hooks/useApi", () => ({
  useList: (path) => ({
    data: path.includes("preferences") ? [mocks.preference] : [mocks.notification],
    loading: false,
    error: null,
    reload: path.includes("preferences") ? mocks.reloadPreferences : mocks.reloadNotifications,
  }),
  useResource: () => ({
    data: { count: 1 }, loading: false, error: null, reload: mocks.reloadUnread,
  }),
}));

function renderPage() {
  return render(<MemoryRouter><NotificationCentre /></MemoryRouter>);
}

describe("notification centre", () => {
  afterEach(() => {
    cleanup();
    mocks.api.post.mockClear();
    mocks.api.patch.mockClear();
    mocks.push.mockClear();
    mocks.reloadNotifications.mockClear();
    mocks.reloadUnread.mockClear();
    mocks.reloadPreferences.mockClear();
  });

  it("marks one alert read through the explicit action", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole("button", { name: "Mark Welcome as read" }));

    await waitFor(() => expect(mocks.api.post).toHaveBeenCalledWith(
      "/communications/notifications/1/mark-read/", {},
    ));
    expect(mocks.push).toHaveBeenCalledWith("Marked as read.", "success");
    expect(mocks.reloadNotifications).toHaveBeenCalled();
    expect(mocks.reloadUnread).toHaveBeenCalled();
  });

  it("saves the chosen inbox types", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole("checkbox", { name: "Academic" }));
    await user.click(screen.getByRole("button", { name: "Save preferences" }));

    await waitFor(() => expect(mocks.api.patch).toHaveBeenCalledWith(
      "/communications/preferences/9/",
      { in_app: true, email: true, sms: false, types: ["SYSTEM", "ACADEMIC"] },
    ));
    expect(mocks.push).toHaveBeenCalledWith("Notification preferences saved.", "success");
  });
});
