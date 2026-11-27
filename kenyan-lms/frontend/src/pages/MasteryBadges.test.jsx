import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import MasteryBadges from "./MasteryBadges";
import PortalMastery from "./PortalMastery";

const mocks = vi.hoisted(() => ({
  reload: vi.fn(async () => {}),
  staff: {
    summary: { learners: 2, badges: 2, earned_badges: 1 },
    rules: {
      badge_bands: [
        { code: "BEGINNING", min_score: "0.25", earned: false },
        { code: "DEVELOPING", min_score: "0.50", earned: false },
        { code: "ACHIEVING", min_score: "0.75", earned: true },
        { code: "EXTENDING", min_score: "1.00", earned: true },
      ],
    },
    badges: [
      {
        learner_id: 4, learner_name: "Amina Ali", admission_number: "MAS-001",
        competency_name: "Numeracy", mastery_level: "EXTENDING", score_percent: 91.7,
        evidence_count: 3, recent_evidence_at: "2026-11-20T09:00:00Z", earned: true,
      },
      {
        learner_id: 5, learner_name: "Brian Otieno", admission_number: "MAS-002",
        competency_name: "Literacy", mastery_level: "DEVELOPING", score_percent: 55,
        evidence_count: 2, recent_evidence_at: "2026-11-18T09:00:00Z", earned: false,
      },
    ],
  },
  mine: {
    summary: { learners: 1, badges: 1, earned_badges: 1 },
    badges: [{
      learner_id: 4,
      competency_name: "Numeracy",
      mastery_level: "EXTENDING",
      score_percent: 91.7,
      evidence_count: 3,
      recent_evidence_at: "2026-11-20T09:00:00Z",
      earned: true,
    }],
  },
}));

vi.mock("../hooks/useApi", () => ({
  useResource: (path) => ({
    data: path === "/analytics/my-mastery/" ? mocks.mine : mocks.staff,
    loading: false,
    error: null,
    reload: mocks.reload,
  }),
}));

describe("mastery badges", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("shows derived bands and learner displays to staff", () => {
    render(<MasteryBadges />);
    expect(screen.getByRole("heading", { name: "Mastery badges" })).toBeTruthy();
    expect(screen.getByRole("cell", { name: "Amina Ali" })).toBeTruthy();
    expect(screen.getByRole("cell", { name: "Numeracy" })).toBeTruthy();
    expect(screen.getByText("Earned")).toBeTruthy();
    expect(screen.getByText(/not a credential/i)).toBeTruthy();
  });

  it("filters the staff table by band", () => {
    render(<MasteryBadges />);
    fireEvent.change(screen.getByLabelText("Band"), { target: { value: "DEVELOPING" } });
    expect(screen.queryByRole("cell", { name: "Amina Ali" })).toBeNull();
    expect(screen.getByRole("cell", { name: "Brian Otieno" })).toBeTruthy();
  });

  it("shows only the signed-in learner's badges in the portal", () => {
    render(<PortalMastery />);
    expect(screen.getByRole("heading", { name: "My mastery badges" })).toBeTruthy();
    expect(screen.getByText("Numeracy")).toBeTruthy();
    expect(screen.queryByText("Literacy")).toBeNull();
    expect(screen.getByText(/not awarded certificates/i)).toBeTruthy();
  });
});
