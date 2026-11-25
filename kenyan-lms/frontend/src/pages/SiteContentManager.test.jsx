import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import SiteContentManager from "./SiteContentManager";
import { DEFAULT_SITE_CONTENT, SITE_STYLE_GROUPS } from "../config/publicSite";

const mocks = vi.hoisted(() => ({
  patch: vi.fn(async (_path, payload) => payload.content),
  upload: vi.fn(async () => ({})),
  del: vi.fn(async () => ({})),
  post: vi.fn(async () => ({})),
  refresh: vi.fn(async () => null),
  push: vi.fn(),
  role: "SUPER_ADMIN",
}));

vi.mock("../services/api", () => ({
  api: { patch: mocks.patch, upload: mocks.upload, del: mocks.del, post: mocks.post },
}));
vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({ user: { role: mocks.role } }),
}));
vi.mock("../context/ToastContext", () => ({
  useToast: () => ({ push: mocks.push }),
}));
vi.mock("../context/SiteContentContext", () => ({
  useSiteContent: () => ({
    content: JSON.parse(JSON.stringify(DEFAULT_SITE_CONTENT)),
    refreshSiteContent: mocks.refresh,
  }),
}));

describe("site content manager", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
    vi.unstubAllGlobals();
    mocks.role = "SUPER_ADMIN";
    mocks.refresh.mockResolvedValue(null);
  });

  it("saves edited wording through the site content endpoint and refreshes the UI", async () => {
    render(<SiteContentManager />);
    fireEvent.click(screen.getByRole("button", { name: "Footer" }));
    fireEvent.change(screen.getByLabelText("Footer name"), {
      target: { value: "Our school footer" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save site content" }));

    await waitFor(() => expect(mocks.patch).toHaveBeenCalledWith(
      "/theming/site-content/",
      {
        content: expect.objectContaining({
          footer: expect.objectContaining({ name: "Our school footer" }),
        }),
      },
    ));
    expect(mocks.refresh).toHaveBeenCalled();
    expect(mocks.push).toHaveBeenCalledWith(
      expect.stringContaining("Site content saved"),
      "success",
    );
  });

  it("keeps photo paths out of the wording editor", () => {
    render(<SiteContentManager />);
    fireEvent.click(screen.getByRole("button", { name: "Homepage introduction" }));
    expect(screen.queryByLabelText("Photo address")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Photos" }));
    expect(screen.getByLabelText("Choose a new photo for Homepage hero photo")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Save site content" })).toBeNull();
  });

  it("publishes an uploaded managed photo immediately", async () => {
    const imageSrc = "/media/site-content/login/login-test.png";
    const content = JSON.parse(JSON.stringify(DEFAULT_SITE_CONTENT));
    content.auth.login.storyImageSrc = imageSrc;
    mocks.upload.mockResolvedValueOnce({ imageSrc, slot: "login", content });

    render(<SiteContentManager />);
    fireEvent.click(screen.getByRole("button", { name: "Photos" }));

    const field = screen.getByLabelText("Choose a new photo for Sign-in story photo").closest(".photo-card");
    const file = new File(["image"], "login.png", { type: "image/png" });
    fireEvent.change(within(field).getByLabelText("Choose a new photo for Sign-in story photo"), {
      target: { files: [file] },
    });
    fireEvent.click(within(field).getByRole("button", { name: "Replace photo" }));

    await waitFor(() => expect(mocks.upload).toHaveBeenCalledWith(
      "/theming/site-content/image/",
      expect.any(FormData),
      "POST",
    ));
    expect(mocks.upload.mock.calls[0][1].get("slot")).toBe("login");
    expect(mocks.upload.mock.calls[0][1].get("image")).toEqual(file);
    expect(mocks.refresh).toHaveBeenCalled();
    expect(mocks.push).toHaveBeenCalledWith(
      expect.stringContaining("Sign-in story photo uploaded and published"),
      "success",
    );
  });

  it("blocks an undersized photo before calling the upload API", async () => {
    vi.stubGlobal("createImageBitmap", vi.fn(async () => ({
      width: 236,
      height: 314,
      close() {},
    })));
    render(<SiteContentManager />);
    fireEvent.click(screen.getByRole("button", { name: "Photos" }));

    const field = screen.getByLabelText("Choose a new photo for Homepage hero photo").closest(".photo-card");
    const file = new File(["small"], "skill-2.jpg", { type: "image/jpeg" });
    fireEvent.change(within(field).getByLabelText("Choose a new photo for Homepage hero photo"), {
      target: { files: [file] },
    });

    await waitFor(() => expect(within(field).getByRole("alert"))
      .toHaveTextContent(/at least 640×360 pixels/));
    const upload = within(field).getByRole("button", { name: "Replace photo" });
    expect(upload.disabled).toBe(true);
    fireEvent.click(upload);
    expect(mocks.upload).not.toHaveBeenCalled();
  });

  it("removes and restores a managed photo through the slot endpoints", async () => {
    const content = JSON.parse(JSON.stringify(DEFAULT_SITE_CONTENT));
    content.auth.login.storyImageSrc = "";
    mocks.del.mockResolvedValueOnce({ content });
    mocks.post.mockResolvedValueOnce({
      content: JSON.parse(JSON.stringify(DEFAULT_SITE_CONTENT)),
    });

    render(<SiteContentManager />);
    fireEvent.click(screen.getByRole("button", { name: "Photos" }));
    const field = screen.getByLabelText("Choose a new photo for Sign-in story photo").closest(".photo-card");

    fireEvent.click(within(field).getByRole("button", { name: "Remove sign-in story photo" }));
    await waitFor(() => expect(mocks.del).toHaveBeenCalledWith(
      "/theming/site-content/image/login/",
    ));

    fireEvent.click(within(field).getByRole("button", {
      name: "Restore the default sign-in story photo",
    }));
    await waitFor(() => expect(mocks.post).toHaveBeenCalledWith(
      "/theming/site-content/image/login/reset/",
      {},
    ));
    expect(mocks.push).toHaveBeenCalledWith(
      expect.stringContaining("Sign-in story photo restored to the default"),
      "success",
    );
  });

  it("lets school admins manage photos in the photo-only Appearance view", () => {
    mocks.role = "ADMIN";
    render(
      <SiteContentManager embedded initialGroup="photos" visibleGroupIds={["photos"]} />,
    );
    expect(screen.getByLabelText("Choose a new photo for Homepage hero photo")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Save site content" })).toBeNull();
  });

  it("lets school admins edit wording and styles but blocks teachers", () => {
    mocks.role = "ADMIN";
    const { rerender } = render(<SiteContentManager />);
    expect(screen.getByRole("button", { name: "Save site content" })).toBeTruthy();

    mocks.role = "TEACHER";
    rerender(<SiteContentManager />);
    expect(screen.getByText(/Only administrators can edit site wording and appearance/i)).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Save site content" })).toBeNull();
  });

  it("saves section-scoped style controls", async () => {
    render(<SiteContentManager groups={SITE_STYLE_GROUPS} />);
    fireEvent.click(screen.getByRole("button", { name: "Homepage hero" }));
    fireEvent.change(screen.getByLabelText(/Background colour/), {
      target: { value: "#123456" },
    });
    fireEvent.change(screen.getByLabelText("Corner style"), {
      target: { value: "16px" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save site content" }));

    await waitFor(() => expect(mocks.patch).toHaveBeenCalledWith(
      "/theming/site-content/",
      {
        content: expect.objectContaining({
          styles: expect.objectContaining({
            hero: expect.objectContaining({ background: "#123456", radius: "16px" }),
          }),
        }),
      },
    ));
  });

  it("blocks an invalid section colour before saving", () => {
    render(<SiteContentManager groups={SITE_STYLE_GROUPS} />);
    fireEvent.click(screen.getByRole("button", { name: "Homepage hero" }));
    fireEvent.change(screen.getByLabelText(/Background colour/), {
      target: { value: "url(javascript:alert(1))" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save site content" }));

    expect(mocks.patch).not.toHaveBeenCalled();
    expect(mocks.push).toHaveBeenCalledWith(
      expect.stringContaining("six-digit hex colour"),
      "error",
    );
  });
});
