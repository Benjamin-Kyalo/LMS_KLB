import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import Home from "./Home";
import { DEFAULT_FOOTER } from "../config/publicSite";

describe("public homepage", () => {
  afterEach(() => {
    cleanup();
    delete window.__KLB_SITE_CONFIG__;
  });

  it("keeps sparse auth links and previews rights and content for the selected role", async () => {
    const user = userEvent.setup();
    const { container } = render(<MemoryRouter><Home /></MemoryRouter>);

    expect(screen.getByRole("heading", { level: 1 }).textContent).toMatch(/Teaching and learning/);
    expect(screen.getByRole("link", { name: "Browse the library" }).getAttribute("href")).toBe("/library");
    expect(screen.getByRole("button", { name: "Students & learners" }).getAttribute("aria-pressed")).toBe("true");
    expect(screen.getByRole("link", { name: "Learner workspace" }).getAttribute("href")).toBe("/login?role=LEARNER");
    expect(screen.getByText("Work only inside your own learner record")).toBeTruthy();
    expect(screen.getByText("My courses and textbook library")).toBeTruthy();

    await user.click(screen.getByRole("button", { name: "Parents & guardians" }));
    expect(screen.getByRole("button", { name: "Parents & guardians" }).getAttribute("aria-pressed")).toBe("true");
    expect(screen.getByRole("link", { name: "Guardian workspace" }).getAttribute("href")).toBe("/login?role=GUARDIAN");
    expect(screen.getByText("View progress for the learners linked to you")).toBeTruthy();
    expect(screen.getByText("Linked learner progress")).toBeTruthy();
    expect(screen.queryByText("Work only inside your own learner record")).toBeNull();

    await user.click(screen.getByRole("button", { name: "Teachers" }));
    expect(screen.getByRole("button", { name: "Teachers" }).getAttribute("aria-pressed")).toBe("true");
    expect(screen.getByRole("link", { name: "Teacher workspace" }).getAttribute("href")).toBe("/login?role=TEACHER");
    expect(screen.getByText("Prepare courses, lessons, assignments and quizzes")).toBeTruthy();
    expect(screen.getByText("Courses, modules and lessons")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Content managers" })).toBeNull();

    const hrefs = [...container.querySelectorAll("a")].map((link) => link.getAttribute("href") || "");
    const sectionLinks = hrefs.filter((href) => href.startsWith("#"));
    expect(hrefs.filter((href) => href === "/register")).toHaveLength(1);
    expect(hrefs.filter((href) => href === "/login")).toHaveLength(1);
    expect(new Set(sectionLinks).size).toBe(sectionLinks.length);
    expect(screen.queryByText(/Quick access/)).toBeNull();
  });

  it("presents three photographed workspaces and an original insights section without the removed static taglines", () => {
    const { container } = render(<MemoryRouter><Home /></MemoryRouter>);

    expect(screen.getByRole("heading", { name: /Three connected ways to use KLB/ })).toBeTruthy();
    expect(screen.getByRole("heading", { name: /A clearer picture of learning/ })).toBeTruthy();
    expect(screen.getByAltText("Learner practising a school skill")).toBeTruthy();
    expect(screen.getByAltText("Education and school records in use")).toBeTruthy();
    expect(screen.getByAltText("Library shelves holding reference books")).toBeTruthy();
    expect(screen.getByAltText("Students and teachers in a school learning space")).toBeTruthy();
    expect(screen.getByAltText("A learner celebrating academic progress")).toBeTruthy();
    expect(container.querySelector('img[src="/images/hero-community.png"]')).toBeTruthy();
    expect(container.querySelector('img[src="/images/insight-success.jpg"]')).toBeTruthy();
    expect(screen.getByText("Attendance, assessments and courses")).toBeTruthy();
    expect(screen.queryByLabelText("Platform at a glance")).toBeNull();
    expect(screen.queryByText(/connected application modules/)).toBeNull();
    expect(screen.queryByText(/shared school database/)).toBeNull();

    expect(screen.queryByText(/Your role decides the registration fields/)).toBeNull();
    expect(screen.queryByText(/Each workspace uses the same records/)).toBeNull();
  });

  it("does not expose the internal administration portal or repeat auth links in the footer", () => {
    const { container } = render(<MemoryRouter><Home /></MemoryRouter>);

    const hrefs = [...container.querySelectorAll("a")].map((link) => link.getAttribute("href") || "");
    expect(hrefs.some((href) => href.includes("/admin"))).toBe(false);
    expect(screen.queryByRole("link", { name: /administration/i })).toBeNull();
    expect(screen.queryByRole("link", { name: /admin sign in/i })).toBeNull();

    const footerLinks = [...container.querySelector("footer").querySelectorAll("a")]
      .map((link) => link.getAttribute("href") || "");
    expect(footerLinks.some((href) => href.startsWith("/login") || href.startsWith("/register"))).toBe(false);
  });

  it("renders the editable footer config and supports a runtime override", () => {
    render(<MemoryRouter><Home /></MemoryRouter>);

    expect(screen.queryByText(/Sample data notice/)).toBeNull();
    expect(screen.getByText(DEFAULT_FOOTER.name)).toBeTruthy();
    DEFAULT_FOOTER.lines.forEach((line) => expect(screen.getByText(line)).toBeTruthy());
    expect(screen.getByRole("link", { name: "Unsplash" }).getAttribute("href")).toBe("https://unsplash.com/license");

    cleanup();
    window.__KLB_SITE_CONFIG__ = {
      content: {
        header: {
          brand: { name: "Custom public brand" },
          links: [{ label: "Custom library", href: "/library" }],
        },
        hero: { imageSrc: "/images/custom-hero.jpg" },
      },
      footer: {
        name: "Custom KLB site",
        lines: ["Custom contact line"],
        credit: { prefix: "Images: ", linkLabel: "Licence", linkHref: "https://example.test/licence", suffix: "" },
      },
    };
    const { container: customContainer } = render(<MemoryRouter><Home /></MemoryRouter>);

    expect(customContainer.querySelector('img[src="/images/custom-hero.jpg"]')).toBeTruthy();
    expect(screen.getByText("Custom public brand")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Custom library" }).getAttribute("href")).toBe("/library");
    expect(screen.getByText("Custom KLB site")).toBeTruthy();
    expect(screen.getByText("Custom contact line")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Licence" }).getAttribute("href")).toBe("https://example.test/licence");
    expect(screen.queryByText(DEFAULT_FOOTER.name)).toBeNull();
  });
});
