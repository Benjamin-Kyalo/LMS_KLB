import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import ThemeManager from "./ThemeManager";

const shades = {
  900: "#1A0F14", 800: "#291720", 700: "#820263", 600: "#D90368",
  500: "#04A777", 400: "#FB8B24", 300: "#FFB067", 200: "#FFD9B8",
  100: "#FFF3E8",
};

const mocks = vi.hoisted(() => ({
  post: vi.fn(async () => ({})),
  patch: vi.fn(async () => ({})),
  del: vi.fn(async () => ({})),
  reload: vi.fn(),
  refreshTheme: vi.fn(async () => ({})),
  push: vi.fn(),
  role: "SUPER_ADMIN",
}));

vi.mock("../services/api", () => ({
  api: { post: mocks.post, patch: mocks.patch, del: mocks.del },
}));
vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({ user: { role: mocks.role } }),
}));
vi.mock("../context/ToastContext", () => ({
  useToast: () => ({ push: mocks.push }),
}));
vi.mock("../context/ThemeContext", () => ({
  useTheme: () => ({
    palette: {
      name: "Plum Harvest",
      description: "Plum and harvest ramp",
      sourceLabel: "color 7.png",
      shades,
    },
    refreshTheme: mocks.refreshTheme,
  }),
}));
vi.mock("../hooks/useApi", () => ({
  useList: () => ({
    data: [
      {
        id: 1, name: "Plum Harvest", slug: "plum-harvest",
        description: "Plum and harvest ramp", source_label: "color 7.png",
        shades, is_active: true, is_builtin: true,
      },
      {
        id: 2, name: "Sage Green", slug: "sage-green",
        description: "Sage ramp", source_label: "colors.png",
        shades: {
          900: "#1E3B2F", 800: "#244C3B", 700: "#2F4A3D", 600: "#3A5F50",
          500: "#6B9080", 400: "#A4C3B2", 300: "#CCE3DE", 200: "#EAF4F4",
          100: "#F6FFF8",
        },
        is_active: false, is_builtin: true,
      },
    ],
    loading: false,
    error: null,
    reload: mocks.reload,
  }),
}));

describe("ThemeManager", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
    mocks.role = "SUPER_ADMIN";
  });

  it("allows school administrators to manage the catalogue", () => {
    mocks.role = "ADMIN";
    render(<ThemeManager />);
    expect(screen.getByRole("heading", { name: /Theme & colours/i })).toBeTruthy();
    expect(screen.queryByText(/Only platform and school administrators/i)).toBeNull();
  });

  it("blocks non-administrators from the catalogue", () => {
    mocks.role = "TEACHER";
    render(<ThemeManager />);
    expect(screen.getByText(/Only platform and school administrators/i)).toBeTruthy();
    expect(screen.queryByRole("heading", { name: /Theme & colours/i })).toBeNull();
  });

  it("activates a palette and refreshes the runtime theme", async () => {
    render(<ThemeManager />);
    fireEvent.click(screen.getByRole("button", { name: "Apply Sage Green palette" }));

    await waitFor(() => expect(mocks.post).toHaveBeenCalledWith(
      "/theming/palettes/2/activate/", {},
    ));
    expect(mocks.refreshTheme).toHaveBeenCalled();
    expect(mocks.reload).toHaveBeenCalled();
  });

  it("rejects text shades that fail contrast before saving", async () => {
    render(<ThemeManager />);
    fireEvent.change(screen.getByLabelText("Palette name"), { target: { value: "Low contrast" } });
    fireEvent.change(screen.getByLabelText("Ramp 700 (text)"), { target: { value: "#FFFFFF" } });
    fireEvent.click(screen.getByRole("button", { name: /Add palette/i }));

    await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());
    expect(screen.getByRole("alert").textContent).toMatch(/contrast/i);
    expect(mocks.post).not.toHaveBeenCalled();
  });

  it("shows a clear place to add and save a custom palette", () => {
    render(<ThemeManager />);
    expect(screen.getByRole("button", { name: "Add your own palette" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Add your own colour set" })).toBeTruthy();
    expect(screen.getByText(/Saved palettes appear in the catalogue with a Custom tag/)).toBeTruthy();
    expect(screen.getByText(/Saving adds the palette to the catalogue shown above/)).toBeTruthy();
  });

  it("onboards a new palette through the catalogue endpoint", async () => {
    render(<ThemeManager />);
    fireEvent.change(screen.getByLabelText("Palette name"), { target: { value: "Aqua" } });
    fireEvent.change(screen.getByLabelText("Source or reference"), { target: { value: "team palette.png" } });
    fireEvent.click(screen.getByRole("button", { name: /Add palette/i }));

    await waitFor(() => expect(mocks.post).toHaveBeenCalledWith(
      "/theming/palettes/",
      expect.objectContaining({ name: "Aqua", source_label: "team palette.png", shade_900: "#1A0F14" }),
    ));
  });
});
