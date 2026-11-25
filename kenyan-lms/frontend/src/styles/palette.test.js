import { afterEach, describe, expect, it } from "vitest";
import {
  applyPaletteToDocument, contrastRatio, normalisePalette, paletteToCssVariables,
} from "./palette";

const sage = {
  id: 2,
  name: "Sage Green",
  slug: "sage-green",
  shades: {
    900: "#1e3b2f", 800: "#244c3b", 700: "#2f4a3d", 600: "#3a5f50",
    500: "#6b9080", 400: "#a4c3b2", 300: "#cce3de", 200: "#eaf4f4",
    100: "#f6fff8",
  },
};

describe("runtime palette helpers", () => {
  it("uses the approved Plum Harvest ramp before the API responds", () => {
    const palette = normalisePalette(null);
    expect(palette.slug).toBe("plum-harvest");
    expect(palette.shades[900]).toBe("#1A0F14");
    expect(palette.shades[800]).toBe("#291720");
    expect(palette.shades[400]).toBe("#FB8B24");
  });

  afterEach(() => {
    document.documentElement.removeAttribute("data-theme");
    Object.keys(paletteToCssVariables(normalisePalette(null))).forEach((name) => {
      document.documentElement.style.removeProperty(name);
    });
    document.head.innerHTML = "";
  });

  it("converts an API palette into CSS variables and chart colours", () => {
    const palette = normalisePalette(sage);
    expect(palette.shades[800]).toBe("#244C3B");
    expect(palette.colors.chart).toEqual(["#244C3B", "#2F4A3D", "#6B9080", "#3A5F50", "#A4C3B2", "#CCE3DE"]);
    expect(palette.colors.attendance.PRESENT).toBe("#244C3B");
    expect(palette.colors.score).toBe("#2F4A3D");
    expect(palette.colors.grid).toBe("#F6FFF8");
  });

  it("applies the selected ramp and browser theme colour to the document", () => {
    document.head.innerHTML = '<meta name="theme-color" content="#023E8A" />';
    applyPaletteToDocument(sage);

    expect(document.documentElement.style.getPropertyValue("--ramp-900")).toBe("#1E3B2F");
    expect(document.documentElement.style.getPropertyValue("--index-tag")).toBe("rgba(36, 76, 59, 0.92)");
    expect(document.documentElement.dataset.theme).toBe("sage-green");
    expect(document.querySelector('meta[name="theme-color"]').getAttribute("content")).toBe("#244C3B");
  });

  it("calculates WCAG contrast for palette validation", () => {
    expect(contrastRatio("#000000", "#FFFFFF")).toBeCloseTo(21, 1);
    expect(contrastRatio("#6B9080", "#FFFFFF")).toBeLessThan(4.5);
    expect(contrastRatio("#1E3B2F", "#FFFFFF")).toBeGreaterThan(4.5);
  });
});
