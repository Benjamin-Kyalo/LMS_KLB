import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Dashboard from "./Dashboard";

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({ user: { id: 1, username: "admin", role: "SCHOOL_ADMIN" } }),
}));

const summary = {
  total_learners: 12,
  active_learners: 10,
  attendance_rate_percent: 87.5,
  average_exam_score: 74.2,
};
const analytics = {
  attendance_status: [],
  attendance_trend: [],
  exam_results: [],
  learner_status: [],
};

vi.mock("../hooks/useApi", () => ({
  useResource: (path) => ({
    data: path.includes("dashboard") ? summary : analytics,
    loading: false,
    error: null,
    reload: vi.fn(),
  }),
}));

vi.mock("../components/ChartCard", () => ({
  default: ({ title }) => <section aria-label={title}>{title}</section>,
}));

describe("Dashboard", () => {
  afterEach(cleanup);

  it("renders clickable KPI cards and the visual report sections", () => {
    render(<MemoryRouter><Dashboard /></MemoryRouter>);
    const learners = screen.getByRole("link", { name: /Learners: 12\. Open details/i });
    expect(learners.getAttribute("href")).toBe("/admin/learners");
    expect(screen.getByRole("link", { name: /Attendance rate: 87\.5%/i }).getAttribute("href")).toBe("/admin/attendance");
    expect(screen.getByRole("button", { name: /Refresh data/i })).toBeTruthy();
    expect(screen.getByRole("region", { name: "Attendance mix" })).toBeTruthy();
    expect(screen.getByRole("region", { name: "Attendance over time" })).toBeTruthy();
    expect(screen.getByRole("region", { name: "Exam performance" })).toBeTruthy();
    expect(screen.getByRole("region", { name: "Learner status" })).toBeTruthy();
    expect(screen.getByRole("link", { name: /Manage learners/i })).toBeTruthy();
  });
});
