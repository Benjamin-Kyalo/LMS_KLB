import { describe, expect, it } from "vitest";
import { firstStyleError, sectionStyleVars } from "./sectionStyles";

describe("section-scoped styles", () => {
  it("turns only allowlisted values into section variables", () => {
    const vars = sectionStyleVars({
      hero: {
        background: "#123456",
        text: "#FFFFFF",
        accent: "#FFB067",
        border: "#ABCDEF",
        radius: "16px",
        spacing: "compact",
        customCss: "body{display:none}",
      },
    }, "hero");

    expect(vars).toEqual({
      "--section-bg": "#123456",
      "--section-ink": "#FFFFFF",
      "--section-accent": "#FFB067",
      "--section-border": "#ABCDEF",
      "--section-radius": "16px",
      "--section-pad-scale": "0.8",
    });
  });

  it("ignores invalid saved values instead of emitting CSS", () => {
    const vars = sectionStyleVars({
      hero: {
        background: "url(javascript:alert(1))",
        radius: "<img src=x onerror=alert(1)>",
        spacing: "huge",
      },
    }, "hero");
    expect(vars).toEqual({});
  });

  it("reports low contrast before an administrator saves", () => {
    expect(firstStyleError({
      hero: { background: "#FFFFFF", text: "#FFFFFF" },
    })).toMatch(/4\.5:1/);
    expect(firstStyleError({
      hero: { background: "#123456", text: "#FFFFFF", radius: "8px" },
    })).toBe("");
  });
});
