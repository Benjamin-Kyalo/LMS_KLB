import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { ThemeProvider, useTheme } from "./ThemeContext";

const mocks = vi.hoisted(() => ({ get: vi.fn() }));
vi.mock("../services/api", () => ({ api: { get: mocks.get } }));

const sage = {
  id: 2,
  name: "Sage Green",
  slug: "sage-green",
  shades: {
    900: "#1E3B2F", 800: "#244C3B", 700: "#2F4A3D", 600: "#3A5F50",
    500: "#6B9080", 400: "#A4C3B2", 300: "#CCE3DE", 200: "#EAF4F4",
    100: "#F6FFF8",
  },
};

describe("ThemeProvider", () => {
  let storage;

  beforeEach(() => {
    storage = new Map();
    vi.stubGlobal("localStorage", {
      getItem: (key) => storage.get(key) ?? null,
      setItem: (key, value) => storage.set(key, value),
      removeItem: (key) => storage.delete(key),
      clear: () => storage.clear(),
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
    vi.unstubAllGlobals();
    document.head.innerHTML = "";
    document.documentElement.removeAttribute("data-theme");
  });

  it("loads the server's active palette and exposes its chart colours", async () => {
    mocks.get.mockResolvedValue(sage);
    document.head.innerHTML = '<meta name="theme-color" content="#023E8A" />';

    const { result } = renderHook(() => useTheme(), { wrapper: ThemeProvider });

    await waitFor(() => expect(result.current.palette.slug).toBe("sage-green"));
    expect(result.current.colors.chart[0]).toBe("#244C3B");
    expect(document.documentElement.style.getPropertyValue("--ramp-800")).toBe("#244C3B");
    expect(document.querySelector('meta[name="theme-color"]').getAttribute("content")).toBe("#244C3B");
  });

  it("keeps a cached palette when the API is unavailable", async () => {
    localStorage.setItem("klb_active_palette", JSON.stringify(sage));
    mocks.get.mockRejectedValue(new TypeError("request failed"));

    const { result } = renderHook(() => useTheme(), { wrapper: ThemeProvider });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.palette.slug).toBe("sage-green");
  });
});
