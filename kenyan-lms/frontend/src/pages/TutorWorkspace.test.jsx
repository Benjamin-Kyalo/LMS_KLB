import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import TutorWorkspace from "./TutorWorkspace";

const mocks = vi.hoisted(() => ({
  reload: vi.fn(async () => {}),
  policy: {
    policy_version: "2026-11-26.1",
    grounded_only: true,
    external_provider_configured: false,
    excluded_records: ["Learner profiles", "Assessment marks and submissions"],
  },
}));

vi.mock("../hooks/useApi", () => ({
  useList: () => ({
    data: [{ id: 1, title: "Fractions practice" }],
    loading: false,
    error: null,
    reload: mocks.reload,
  }),
  useResource: (path) => {
    if (path.includes("/health/")) {
      return {
        data: { provider: "local", grounded_only: true, policy: mocks.policy },
        loading: false,
        error: null,
        reload: mocks.reload,
      };
    }
    return {
      data: [{
        id: 1,
        role: "TUTOR",
        body: "A grounded answer",
        sources: [],
        suggestions: [],
        policy: { policy_version: "2026-11-26.1" },
      }],
      loading: false,
      error: null,
      reload: mocks.reload,
    };
  },
}));
vi.mock("../context/ToastContext", () => ({ useToast: () => ({ push: vi.fn() }) }));
vi.mock("../context/SiteContentContext", () => ({
  useSiteContent: () => ({ content: { portal: {} } }),
}));
vi.mock("../styles/sectionStyles", () => ({ useSectionStyle: () => ({}) }));
vi.mock("../services/api", () => ({ api: { post: vi.fn() } }));

describe("governed tutor workspace", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("shows the active policy and the policy version on grounded answers", () => {
    render(<TutorWorkspace />);
    expect(screen.getByRole("heading", { name: "Curriculum tutor" })).toBeTruthy();
    expect(screen.getByText(/Active provider:/)).toBeTruthy();
    expect(screen.getByText("local")).toBeTruthy();
    expect(screen.getByText(/Policy v2026-11-26.1/)).toBeTruthy();
    expect(screen.getByText(/Learner, assessment, fee and message records are never sent/)).toBeTruthy();
    expect(screen.getByText(/No external AI provider is configured/)).toBeTruthy();
    expect(screen.getByText(/Answer policy v2026-11-26.1/)).toBeTruthy();
  });
});
