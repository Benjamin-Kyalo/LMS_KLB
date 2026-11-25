import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import AppearanceManager from "./AppearanceManager";
import { DEFAULT_SITE_CONTENT } from "../config/publicSite";

const mocks = vi.hoisted(() => ({
  refresh: vi.fn(async () => null),
  push: vi.fn(),
  role: "SUPER_ADMIN",
}));

vi.mock("../services/api", () => ({
  api: {
    get: vi.fn(async () => ({})),
    patch: vi.fn(async (_path, payload) => payload.content),
    post: vi.fn(async () => ({})),
    del: vi.fn(async () => ({})),
    upload: vi.fn(async () => ({})),
  },
}));
vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({ user: { role: mocks.role } }),
}));
vi.mock("../context/ToastContext", () => ({
  useToast: () => ({ push: mocks.push }),
}));
vi.mock("../context/SiteContentContext", () => ({
  useSiteContent: () => ({
    content: JSON.parse(JSON.stringify(DEFAULT_SITE_CONTENT)),
    refreshSiteContent: mocks.refresh,
  }),
}));
vi.mock("../context/ThemeContext", () => ({
  useTheme: () => ({
    palette: {
      name: "Plum Harvest",
      description: "Default palette",
      shades: { 100: "#eee", 300: "#ccc", 400: "#999", 500: "#777", 600: "#555", 700: "#333", 800: "#222", 900: "#111" },
      sourceLabel: "Built in",
    },
    refreshTheme: vi.fn(async () => {}),
  }),
}));
vi.mock("../hooks/useApi", () => ({
  useList: () => ({ data: [], loading: false, error: null, reload: vi.fn() }),
}));

describe("appearance manager", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
    mocks.role = "SUPER_ADMIN";
  });

  it("opens the requested legacy section in one appearance page", () => {
    render(<AppearanceManager initialTab="photos" />);
    expect(screen.getByRole("heading", { name: "Site appearance" })).toBeTruthy();
    const tabs = screen.getByRole("navigation", { name: "Appearance sections" });
    expect(within(tabs).getByRole("button", { name: /Photos/ }).getAttribute("aria-pressed")).toBe("true");
    expect(screen.getByLabelText("Choose a new photo for Homepage hero photo")).toBeTruthy();
  });

  it("switches between colours, photos, words and styles without leaving the page", () => {
    render(<AppearanceManager />);
    fireEvent.click(screen.getByRole("button", { name: /Colours/ }));
    expect(screen.getByText("Palette catalogue")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: /Words/ }));
    expect(screen.getByRole("button", { name: "Footer" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Save site content" })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: /Styles/ }));
    expect(screen.getByRole("button", { name: "Homepage hero" })).toBeTruthy();
    expect(screen.getByLabelText(/Background colour/)).toBeTruthy();
  });

  it("offers photos, words and styles to school administrators", () => {
    mocks.role = "ADMIN";
    render(<AppearanceManager initialTab="photos" />);
    const tabs = screen.getByRole("navigation", { name: "Appearance sections" });
    expect(within(tabs).getByRole("button", { name: /Photos/ })).toBeTruthy();
    expect(within(tabs).getByRole("button", { name: /Words/ })).toBeTruthy();
    expect(within(tabs).getByRole("button", { name: /Styles/ })).toBeTruthy();
    expect(screen.getByLabelText("Choose a new photo for Homepage hero photo")).toBeTruthy();
    expect(screen.queryByText(/platform administrator only/)).toBeNull();
  });
});
