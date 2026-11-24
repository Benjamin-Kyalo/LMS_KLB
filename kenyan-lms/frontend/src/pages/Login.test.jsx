import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Login from "./Login";

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({ signIn: vi.fn(), loading: false, error: null }),
}));

describe("public sign-in page", () => {
  afterEach(cleanup);

  it("does not advertise the internal administration portal", () => {
    const { container } = render(<MemoryRouter><Login /></MemoryRouter>);

    expect(screen.getByRole("heading", { level: 1, name: "Welcome back" })).toBeTruthy();
    expect([...container.querySelectorAll("a")].some((link) => (link.getAttribute("href") || "").includes("/admin"))).toBe(false);
  });

  it("still provides the dedicated administration sign-in form at its internal route", () => {
    render(<MemoryRouter><Login variant="admin" /></MemoryRouter>);

    expect(screen.getByRole("heading", { level: 1, name: "Administrator sign in" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Redeem an administrator invitation" }).getAttribute("href")).toBe("/admin/signup");
  });
});
