import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import PortalHome from "./PortalHome";

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({
    user: {
      id: 8, username: "amina", first_name: "Amina", role: "GUARDIAN",
      onboarding: { is_complete: false },
    },
  }),
}));
vi.mock("../context/ThemeContext", () => ({
  useTheme: () => ({ colors: { attendance: {}, score: "var(--primary)" } }),
}));
vi.mock("../hooks/useApi", () => ({
  useList: () => ({ data: [], loading: false, error: null, reload: vi.fn() }),
}));
vi.mock("../services/api", () => ({ api: { get: vi.fn() } }));
vi.mock("../components/ChartCard", () => ({
  default: ({ title }) => <section aria-label={title}>{title}</section>,
}));

describe("guardian portal home", () => {
  afterEach(cleanup);

  it("explains that learner data stays hidden until a link is verified", () => {
    render(<MemoryRouter><PortalHome /></MemoryRouter>);
    expect(screen.getByRole("heading", { name: /Habari, Amina/ })).toBeTruthy();
    expect(screen.getByText(/Reports open after your school verifies the link/)).toBeTruthy();
    expect(screen.getByRole("link", { name: "Complete setup →" }).getAttribute("href")).toBe("/onboarding");
  });
});
