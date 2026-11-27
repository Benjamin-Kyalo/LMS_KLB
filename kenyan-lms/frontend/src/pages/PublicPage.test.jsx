import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import PublicPage from "./PublicPage";
import { DEFAULT_SITE_CONTENT } from "../config/publicSite";

const mocks = vi.hoisted(() => ({ post: vi.fn() }));

vi.mock("../services/api", () => ({ api: { post: mocks.post } }));

function renderPage(page, route = "/") {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <PublicPage page={page} />
    </MemoryRouter>,
  );
}

async function fillContactForm(user) {
  await user.type(screen.getByLabelText("Full name"), "Amina Test");
  await user.type(screen.getByLabelText("Email address"), "amina@example.test");
  await user.type(screen.getByLabelText("Phone number"), "0712345678");
  await user.type(screen.getByLabelText("Organisation or school"), "Mwangaza School");
  await user.selectOptions(screen.getByLabelText("Enquiry category"), "School registration");
  await user.type(screen.getByLabelText("Subject"), "Registration help");
  await user.type(screen.getByLabelText("Message"), "Please tell us how to register.");
}

describe("public information pages", () => {
  afterEach(() => {
    cleanup();
    delete window.__KLB_SITE_CONFIG__;
    vi.clearAllMocks();
  });

  it("renders managed about and role page copy without inventing wording", () => {
    renderPage("about");

    expect(screen.getByRole("heading", { level: 1, name: "About KLB Elimu" })).toBeTruthy();
    expect(screen.getByText("Learning deserves a thoughtful digital home.")).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Our approach" })).toBeTruthy();
    expect(screen.getByText("Learning first")).toBeTruthy();
    expect(screen.getByText(/KLB Elimu is being designed with attention/)).toBeTruthy();

    cleanup();
    renderPage("teachers");

    expect(screen.getByRole("heading", { level: 1, name: "Your teaching workspace." })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Features" })).toBeTruthy();
    expect(screen.getByText("Prepare and organise lessons.")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Access Teacher Portal" }).getAttribute("href"))
      .toBe("/login?role=TEACHER");
  });

  it("renders legal pages from supplied content and keeps legal-review notes visible", () => {
    renderPage("terms");

    expect(screen.getByRole("heading", { level: 1, name: "Terms of Use" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Using the platform" })).toBeTruthy();
    expect(screen.getByText("Keep account credentials private.")).toBeTruthy();
    expect(screen.getByText(/final Terms of Use must be reviewed/)).toBeTruthy();
    expect(screen.queryByText(/Do not promise a response time/)).toBeNull();

    cleanup();
    renderPage("acceptableUse");

    expect(screen.getByRole("heading", { level: 1, name: "Acceptable Use Policy" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Expected conduct" })).toBeTruthy();
    expect(screen.getByText("Protect your account credentials.")).toBeTruthy();
    expect(screen.getByText(/final Acceptable Use Policy must be reviewed/)).toBeTruthy();

    cleanup();
    renderPage("privacy");

    expect(screen.getByRole("heading", { level: 1, name: "Your information deserves care." }))
      .toBeTruthy();
    expect(screen.getByRole("heading", { name: "Important privacy principles" })).toBeTruthy();
    expect(screen.getByText("Collect only necessary information.")).toBeTruthy();
    expect(screen.getByText(/final Privacy Notice, Terms of Use/)).toBeTruthy();

    cleanup();
    renderPage("accessibility");

    expect(screen.getByRole("heading", { level: 1, name: "Make Learning Work for You" }))
      .toBeTruthy();
    expect(screen.getByRole("heading", { name: "Accessibility settings" })).toBeTruthy();
    expect(screen.getByText("Screen-reader compatibility")).toBeTruthy();
  });

  it("filters help articles with a visible count and the managed empty state", async () => {
    const user = userEvent.setup();
    renderPage("help");

    const search = screen.getByRole("searchbox", { name: "What would you like help with?" });
    expect(screen.getByText("32 results")).toBeTruthy();

    await user.type(search, "password");
    expect(screen.getByText("2 results")).toBeTruthy();
    expect(screen.getByText("How to reset a password.")).toBeTruthy();
    expect(screen.getByText("How to change a password.")).toBeTruthy();
    expect(screen.queryByText("How to register a school.")).toBeNull();

    await user.clear(search);
    await user.type(search, "nothing matches this");
    expect(screen.getByText("0 results")).toBeTruthy();
    expect(screen.getByText(DEFAULT_SITE_CONTENT.publicPages.help.noResults)).toBeTruthy();
  });

  it("uses accessible disclosure semantics for frequently asked questions", async () => {
    const user = userEvent.setup();
    renderPage("faq");

    const summary = screen.getByText("What is KLB Elimu?");
    const details = summary.closest("details");
    expect(details).toBeTruthy();
    expect(details.open).toBe(false);

    await user.click(summary);
    expect(details.open).toBe(true);
    expect(details).toHaveTextContent("proposed digital learning ecosystem");
  });

  it("posts the contact form and shows the managed confirmation with the returned reference", async () => {
    const user = userEvent.setup();
    let resolvePost;
    mocks.post.mockImplementation(() => new Promise((resolve) => { resolvePost = resolve; }));
    renderPage("contact");

    await fillContactForm(user);
    await user.click(screen.getByRole("button", { name: "Send Enquiry" }));

    expect(mocks.post).toHaveBeenCalledWith("/core/public-enquiries/", expect.objectContaining({
      full_name: "Amina Test",
      email: "amina@example.test",
      phone: "0712345678",
      organisation: "Mwangaza School",
      category: "School registration",
      subject: "Registration help",
      message: "Please tell us how to register.",
    }));
    expect(screen.getByText("Sending enquiry…")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Send Enquiry" })).toBeTruthy();

    resolvePost({ reference: "ENQ-2026-001" });
    await waitFor(() => expect(screen.getByText("ENQ-2026-001")).toBeTruthy());
    expect(screen.getByText(DEFAULT_SITE_CONTENT.publicPages.contact.confirmation)).toBeTruthy();
    expect(screen.queryByText(/Do not promise a response time/)).toBeNull();
  });

  it("shows a professional managed error and preserves values when the enquiry fails", async () => {
    const user = userEvent.setup();
    mocks.post.mockRejectedValue(new Error('{"detail":"raw JSON"} <script>bad</script>'));
    renderPage("contact");

    await fillContactForm(user);
    await user.click(screen.getByRole("button", { name: "Send Enquiry" }));

    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent(
      DEFAULT_SITE_CONTENT.messages.errors.somethingWrong,
    ));
    expect(screen.getByLabelText("Full name")).toHaveValue("Amina Test");
    expect(screen.getByLabelText("Message")).toHaveValue("Please tell us how to register.");
    expect(screen.queryByText(/raw JSON/)).toBeNull();
    expect(screen.queryByText(/<script>/)).toBeNull();
    expect(screen.getByRole("button", { name: "Send Enquiry" })).toBeTruthy();
    expect(screen.queryByText("Sending enquiry…")).toBeNull();
  });

  it("keeps managed links safe when an administrator supplies an unsafe address", () => {
    window.__KLB_SITE_CONFIG__ = {
      content: {
        publicPages: {
          schools: { actionLabel: "External guide", actionHref: "https://example.test/schools" },
        },
      },
    };
    renderPage("schools");

    const external = screen.getByRole("link", { name: "External guide" });
    expect(external.getAttribute("href")).toBe("https://example.test/schools");
    expect(external.getAttribute("target")).toBe("_blank");
    expect(external.getAttribute("rel")).toBe("noopener noreferrer");
    expect(external.getAttribute("aria-describedby")).toBeTruthy();

    cleanup();
    window.__KLB_SITE_CONFIG__ = {
      content: {
        publicPages: {
          schools: { actionLabel: "Unsafe guide", actionHref: "javascript:alert(1)" },
        },
      },
    };
    renderPage("schools");
    expect(screen.getByRole("link", { name: "Unsafe guide" }).getAttribute("href")).toBe("/");
  });
});
