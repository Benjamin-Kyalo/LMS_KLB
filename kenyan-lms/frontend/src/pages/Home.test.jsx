import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import Home from "./Home";
import { DEFAULT_FOOTER, DEFAULT_SITE_CONTENT } from "../config/publicSite";

describe("public homepage", () => {
  afterEach(() => {
    cleanup();
    delete window.__KLB_SITE_CONFIG__;
  });

  it("keeps sparse auth links and previews rights and content for the selected role", async () => {
    const user = userEvent.setup();
    const { container } = render(<MemoryRouter><Home /></MemoryRouter>);

    expect(screen.getByRole("heading", { level: 1 }).textContent)
      .toMatch(/Give every lesson somewhere to go/);
    expect(screen.getByRole("link", { name: "Explore the Digital Library" }).getAttribute("href"))
      .toBe("/library");
    expect(screen.getByRole("button", { name: "Students & learners" }).getAttribute("aria-pressed"))
      .toBe("true");
    expect(screen.getByRole("link", { name: "Learner workspace" }).getAttribute("href"))
      .toBe("/login?role=LEARNER");
    expect(screen.getByText("Work only inside your own learner record")).toBeTruthy();
    expect(screen.getByText("My courses and textbook library")).toBeTruthy();

    await user.click(screen.getByRole("button", { name: "Parents & guardians" }));
    expect(screen.getByRole("button", { name: "Parents & guardians" }).getAttribute("aria-pressed"))
      .toBe("true");
    expect(screen.getByRole("link", { name: "Guardian workspace" }).getAttribute("href"))
      .toBe("/login?role=GUARDIAN");
    expect(screen.getByText("View progress for the learners linked to you")).toBeTruthy();
    expect(screen.getByText("Linked learner progress")).toBeTruthy();
    expect(screen.queryByText("Work only inside your own learner record")).toBeNull();

    await user.click(screen.getByRole("button", { name: "Teachers" }));
    expect(screen.getByRole("button", { name: "Teachers" }).getAttribute("aria-pressed"))
      .toBe("true");
    expect(screen.getByRole("link", { name: "Teacher workspace" }).getAttribute("href"))
      .toBe("/login?role=TEACHER");
    expect(screen.getByText("Prepare courses, lessons, assignments and quizzes")).toBeTruthy();
    expect(screen.getByText("Courses, modules and lessons")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Content managers" })).toBeNull();

    const hrefs = [...container.querySelectorAll("a")].map((link) => link.getAttribute("href") || "");
    const quickNav = screen.getByRole("navigation", { name: DEFAULT_SITE_CONTENT.quickLinks.title });
    const quickHrefs = [...quickNav.querySelectorAll("a")].map((link) => link.getAttribute("href"));
    expect(hrefs.filter((href) => href === "/register")).toHaveLength(0);
    expect(screen.getAllByRole("link", { name: DEFAULT_SITE_CONTENT.header.signInLabel }))
      .toHaveLength(1);
    expect(new Set(quickHrefs).size).toBe(quickHrefs.length);
    DEFAULT_SITE_CONTENT.quickLinks.links.forEach((item) => expect(quickHrefs).toContain(item.href));
    expect(screen.queryByText(/Quick access/)).toBeNull();
  }, 20000);

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

  it("offers an accessible menu and the new guided discovery sections", async () => {
    const user = userEvent.setup();
    const { container } = render(<MemoryRouter><Home /></MemoryRouter>);

    expect(screen.getByRole("heading", { name: "Built for the way schools work" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Start with three clear steps" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Find the right resource faster" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Questions people ask first" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Search the library" }).getAttribute("href"))
      .toBe("/library");

    const toggle = screen.getByRole("button", { name: "Menu" });
    const nav = container.querySelector(".public-nav");
    expect(toggle.getAttribute("aria-expanded")).toBe("false");
    await user.click(toggle);
    expect(toggle.getAttribute("aria-expanded")).toBe("true");
    expect(nav.className).toContain("is-open");
    await user.keyboard("{Escape}");
    expect(toggle.getAttribute("aria-expanded")).toBe("false");
    expect(nav.className).not.toContain("is-open");
    expect(screen.getByRole("button", { name: "Menu" })).toBeTruthy();
  });

  it("does not expose the internal administration portal or repeat auth links in the footer", () => {
    const { container } = render(<MemoryRouter><Home /></MemoryRouter>);

    const hrefs = [...container.querySelectorAll("a")].map((link) => link.getAttribute("href") || "");
    expect(hrefs.some((href) => href.includes("/admin"))).toBe(false);
    expect(screen.queryByRole("link", { name: /administration/i })).toBeNull();
    expect(screen.queryByRole("link", { name: /admin sign in/i })).toBeNull();

    const footerLinks = [...container.querySelector("footer").querySelectorAll("a")]
      .map((link) => link.getAttribute("href") || "");
    expect(footerLinks.some((href) => href.startsWith("/login") || href.startsWith("/register")))
      .toBe(false);
  });

  it("uses safe external links for managed calls to action", () => {
    window.__KLB_SITE_CONFIG__ = {
      content: {
        hero: {
          primaryLabel: "Visit KLB",
          primaryHref: "https://klb.co.ke",
        },
        spotlight: {
          actionLabel: "External guide",
          actionHref: "javascript:alert(1)",
        },
      },
    };
    render(<MemoryRouter><Home /></MemoryRouter>);

    const external = screen.getByRole("link", { name: "Visit KLB" });
    expect(external.getAttribute("href")).toBe("https://klb.co.ke");
    expect(external.getAttribute("target")).toBe("_blank");
    expect(external.getAttribute("rel")).toBe("noopener noreferrer");
    expect(external.getAttribute("aria-describedby")).toBeTruthy();

    expect(screen.getByRole("link", { name: "External guide" }).getAttribute("href")).toBe("/");
  });

  it("renders the editable footer config and supports a runtime override", () => {
    const renderResult = render(<MemoryRouter><Home /></MemoryRouter>);

    const footer = renderResult.container.querySelector("footer");
    expect(screen.queryByText(/Sample data notice/)).toBeNull();
    expect(within(footer).getByText(DEFAULT_FOOTER.name)).toBeTruthy();
    DEFAULT_FOOTER.lines.forEach((line) => expect(within(footer).getByText(line)).toBeTruthy());
    expect(within(footer).getByRole("link", { name: "Unsplash" }).getAttribute("href"))
      .toBe("https://unsplash.com/license");

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
    const customFooter = customContainer.querySelector("footer");

    expect(customContainer.querySelector('img[src="/images/custom-hero.jpg"]')).toBeTruthy();
    expect(screen.getByText("Custom public brand")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Custom library" }).getAttribute("href"))
      .toBe("/library");
    expect(within(customFooter).getByText("Custom KLB site")).toBeTruthy();
    expect(within(customFooter).getByText("Custom contact line")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Licence" }).getAttribute("href"))
      .toBe("https://example.test/licence");
    expect(within(customFooter).queryByText(DEFAULT_FOOTER.name)).toBeNull();
  });

  it("adds ten more guided-discovery upgrades with accessible behaviour", async () => {
    const user = userEvent.setup();
    const scrollTo = vi.fn();
    window.scrollTo = scrollTo;
    const { container } = render(<MemoryRouter><Home /></MemoryRouter>);

    // 1. Keyboard bypass and 2. a quiet reading-position indicator.
    expect(screen.getByRole("link", { name: "Skip to homepage content" }).getAttribute("href"))
      .toBe("#home-content");
    expect(container.querySelector(".reading-progress")).toBeTruthy();

    // 3. A dismissible announcement with a managed internal action.
    expect(screen.getByRole("complementary", { name: "Site announcement" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Explore the Library" }).getAttribute("href"))
      .toBe("/library");
    await user.click(screen.getByRole("button", { name: "Dismiss announcement" }));
    expect(screen.queryByRole("complementary", { name: "Site announcement" })).toBeNull();

    // 4. An on-page quick-link strip with safe, unique destinations.
    expect(screen.getByRole("navigation", { name: "On this page" })).toBeTruthy();
    const accessLinks = screen.getAllByRole("link", { name: "See role access" });
    expect(accessLinks.length).toBeGreaterThanOrEqual(1);
    expect(accessLinks.every((link) => link.getAttribute("href") === "/#access")).toBe(true);

    // 5. A short preparation checklist beside the three steps.
    expect(screen.getByRole("heading", { name: "Have these ready" })).toBeTruthy();
    expect(screen.getByText("The account issued by your school")).toBeTruthy();

    // 6. Everyday routines and 7. a plain-language access table.
    expect(screen.getByRole("heading", { name: "Small routines, one shared record" })).toBeTruthy();
    expect(screen.getByText("Teachers prepare courses, materials and assessments in one place."))
      .toBeTruthy();
    const accessTable = screen.getByRole("table", { name: "Who sees what by role" });
    expect(accessTable.querySelectorAll("thead th")).toHaveLength(3);
    expect(accessTable.querySelectorAll("tbody tr")).toHaveLength(3);
    expect(screen.getByRole("rowheader", { name: "Guardians" })).toBeTruthy();

    // 8. A usability commitment that matches the implemented behaviour.
    expect(screen.getByRole("heading", { name: "Easy to use, by design" })).toBeTruthy();
    expect(screen.getByText("Every action has a visible focus and an accessible name."))
      .toBeTruthy();

    // 9. A support callout that points back to school-administered help.
    expect(screen.getByRole("heading", { name: "Help starts with your school" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Read common questions" }).getAttribute("href"))
      .toBe("/#faq");

    // 10. A labelled back-to-top control that respects reduced motion.
    const backToTop = screen.getByRole("button", { name: "Back to top" });
    await user.click(backToTop);
    expect(scrollTo).toHaveBeenCalledWith(expect.objectContaining({ top: 0 }));
  });

  it("renders every managed blueprint section at its stable anchor", () => {
    const { container } = render(<MemoryRouter><Home /></MemoryRouter>);

    expect(screen.getByText("Built around learning. Designed for Kenyan schools.")).toBeTruthy();
    expect(screen.getByRole("heading", { name: "A better-connected way to learn." })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Everything learning needs, brought closer." }))
      .toBeTruthy();
    expect(screen.getByRole("heading", { name: "A good book can take learning further." }))
      .toBeTruthy();
    expect(screen.getByRole("heading", { name: "Less time organising. More time teaching." }))
      .toBeTruthy();
    expect(screen.getByRole("heading", { name: "Your next discovery starts here." })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Be part of the learning journey." })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Getting started is straightforward." })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Make room for more learning." })).toBeTruthy();

    ["introduction", "capabilities", "library", "teachers", "learners", "parents", "how-it-works", "faq"]
      .forEach((id) => expect(container.querySelector(`#${id}`)).toBeTruthy());
  });
});
