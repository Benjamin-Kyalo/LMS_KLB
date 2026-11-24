import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import ChartCard from "./ChartCard";

vi.mock("recharts", () => ({
  ResponsiveContainer: ({ children }) => <div data-testid="responsive">{children}</div>,
  BarChart: ({ children }) => <div data-testid="bar-chart">{children}</div>,
  Bar: ({ dataKey }) => <div data-testid="bar" data-key={dataKey} />,
  LineChart: ({ children }) => <div data-testid="line-chart">{children}</div>,
  Line: ({ dataKey }) => <div data-testid="line" data-key={dataKey} />,
  PieChart: ({ children }) => <div data-testid="pie-chart">{children}</div>,
  Pie: () => <div data-testid="pie" />,
  Cell: () => <div />,
  CartesianGrid: () => <div />,
  Legend: () => <div />,
  Tooltip: () => <div />,
  XAxis: () => <div />,
  YAxis: () => <div />,
}));

describe("ChartCard", () => {
  afterEach(cleanup);

  it("renders a responsive bar chart with the requested series", () => {
    render(
      <ChartCard
        title="Attendance"
        data={[{ label: "Mon", PRESENT: 3 }]}
        xKey="label"
        series={[{ key: "PRESENT", label: "Present" }]}
      />
    );
    expect(screen.getByTestId("responsive")).toBeTruthy();
    expect(screen.getByTestId("bar-chart")).toBeTruthy();
    expect(screen.getByTestId("bar").getAttribute("data-key")).toBe("PRESENT");
  });

  it("shows a friendly empty state instead of a blank chart", () => {
    render(<ChartCard title="Exams" data={[]} emptyText="Nothing recorded." />);
    expect(screen.getByText("Nothing recorded.")).toBeTruthy();
    expect(screen.queryByTestId("responsive")).toBeNull();
  });
});
