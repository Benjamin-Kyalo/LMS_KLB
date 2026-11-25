import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Login from "./Login";

const mocks = vi.hoisted(() => ({
  signIn: vi.fn(async () => ({ user: { id: 1, role: "LEARNER" } })),
}));

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({ signIn: mocks.signIn, loading: false, error: null }),
}));

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/login"]}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/onboarding" element={<div>First-time setup</div>} />
        <Route path="/portal" element={<div>Learner portal</div>} />
      </Routes>
    </MemoryRouter>
  );
}

describe("public sign-in page", () => {
  afterEach(() => {
    cleanup();
    delete window.__KLB_SITE_CONFIG__;
    mocks.signIn.mockClear();
  });

  it("does not advertise the internal administration portal", () => {
    const { container } = renderPage();
    expect(container.querySelector('img[src="/images/signin-time.jpg"]')).toBeTruthy();
    expect(screen.getByRole("heading", { level: 2, name: "Welcome back" })).toBeTruthy();
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect([...container.querySelectorAll("a")].some((link) => (link.getAttribute("href") || "").includes("/admin"))).toBe(false);
  });

  it("still provides the dedicated administration sign-in form at its internal route", () => {
    render(<MemoryRouter><Login variant="admin" /></MemoryRouter>);
    expect(screen.getByRole("heading", { level: 2, name: "Administrator sign in" })).toBeTruthy();
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(screen.getByRole("link", { name: "Redeem an administrator invitation" }).getAttribute("href")).toBe("/admin/signup");
  });

  it("uses editable brand and sign in wording", () => {
    window.__KLB_SITE_CONFIG__ = {
      content: {
        header: { brand: { name: "Custom learning brand" } },
        auth: {
          login: {
            storyImageSrc: "/media/site-content/login/custom.png",
            publicHeading: "Custom sign in heading",
            storyCopy: "Custom sign in story",
            footnote: "Custom sign in footnote",
            publicIntro: "Custom sign in note",
          },
        },
      },
    };
    const { container } = renderPage();

    expect(container.querySelector('img[src="/media/site-content/login/custom.png"]')).toBeTruthy();
    expect(screen.getByText("Custom learning brand")).toBeTruthy();
    expect(screen.getByRole("heading", { level: 1, name: "Custom sign in heading" })).toBeTruthy();
    expect(screen.getByText("Custom sign in story")).toBeTruthy();
    expect(screen.getByText("Custom sign in footnote")).toBeTruthy();
    expect(screen.getByText("Custom sign in note")).toBeTruthy();
  });

  it("sends an incomplete account to first-time setup", async () => {
    const user = userEvent.setup();
    mocks.signIn.mockResolvedValueOnce({
      user: { id: 4, role: "GUARDIAN", onboarding: { is_complete: false } },
    });
    renderPage();

    await user.type(screen.getByLabelText("Username"), "amina");
    await user.type(screen.getByLabelText("Password"), "StrongPass123!");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => expect(screen.getByText("First-time setup")).toBeTruthy());
  });
});
