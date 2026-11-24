import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import SampleDataBadge from "./SampleDataBadge";

describe("SampleDataBadge", () => {
  afterEach(cleanup);

  it("marks the original demo institution as sample data", () => {
    render(<SampleDataBadge code="DEMO01" />);
    expect(screen.getByText("SAMPLE DATA")).toBeTruthy();
  });

  it("marks seeded institutions as sample data", () => {
    render(<SampleDataBadge code="SMP01" />);
    expect(screen.getByText("SAMPLE DATA")).toBeTruthy();
  });

  it("stays hidden for ordinary institutions", () => {
    const { container } = render(<SampleDataBadge code="KIB01" />);
    expect(container.textContent).toBe("");
  });

  it("stays hidden when there is no institution", () => {
    const { container } = render(<SampleDataBadge />);
    expect(container.textContent).toBe("");
  });
});
