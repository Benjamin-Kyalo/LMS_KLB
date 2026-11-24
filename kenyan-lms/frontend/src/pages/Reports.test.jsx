import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Reports from "./Reports";

const mocks = vi.hoisted(() => {
  const report = {
    learner: { id: 7, name: "Amina Otieno", admission_number: "ADM-001", class: "Grade 4", institution: "Demo School" },
    attendance: { PRESENT: 4, ABSENT: 0, LATE: 1, EXCUSED: 0 },
    exams: [{ label: "Term 1 Maths", date: "2026-03-20", score: 78, max_score: 100, percentage: 78, grade: "B" }],
    average_score: 78,
    permissions: { attendance: true, academics: true },
  };
  return { report, get: vi.fn(async () => report) };
});

vi.mock("../services/api", () => ({ api: { get: mocks.get } }));
vi.mock("../hooks/useApi", () => ({
  useList: () => ({
    data: [{ id: 7, learner_name: "Amina Otieno", admission_number: "ADM-001" }],
    loading: false,
  }),
}));
vi.mock("../components/ChartCard", () => ({
  default: ({ title }) => <section aria-label={title}>{title}</section>,
}));

describe("Reports", () => {
  afterEach(() => {
    cleanup();
    mocks.get.mockClear();
  });

  it("loads a learner report and renders visual and tabular detail", async () => {
    render(<MemoryRouter><Reports /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText("Amina Otieno")).toBeTruthy());
    expect(screen.getByLabelText("Choose a learner")).toBeTruthy();
    expect(screen.getByRole("region", { name: "Attendance" })).toBeTruthy();
    expect(screen.getByRole("region", { name: "Exam scores" })).toBeTruthy();
    expect(screen.getByText("Term 1 Maths")).toBeTruthy();
    expect(mocks.get).toHaveBeenCalledWith("/reports/learner/7/");
  });
});
