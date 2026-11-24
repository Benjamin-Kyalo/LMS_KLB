import { describe, it, expect } from "vitest";
import { formatDate } from "./format";

describe("formatDate", () => {
  it("returns a dash for empty values", () => {
    expect(formatDate(null)).toBe("—");
    expect(formatDate("")).toBe("—");
  });
  it("formats a valid date", () => {
    const out = formatDate("2026-01-15");
    expect(out).toContain("2026");
    expect(out).toContain("Jan");
  });
});
