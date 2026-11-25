import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { SiteContentProvider, useSiteContent } from "./SiteContentContext";

const mocks = vi.hoisted(() => ({ get: vi.fn() }));

vi.mock("../services/api", () => ({ api: { get: mocks.get } }));

// jsdom 27 no longer exposes localStorage in every Node runtime. The provider
// only needs a small key/value surface, so tests supply a deterministic one.
function installStorage() {
  const store = new Map();
  Object.defineProperty(window, "localStorage", {
    configurable: true,
    value: {
      getItem: (key) => (store.has(key) ? store.get(key) : null),
      setItem: (key, value) => store.set(key, String(value)),
      removeItem: (key) => store.delete(key),
      clear: () => store.clear(),
    },
  });
}

function Consumer() {
  const { content } = useSiteContent();
  return <div>{`${content.footer.name}|${content.roles.title}`}</div>;
}

describe("site content provider", () => {
  beforeEach(() => {
    installStorage();
    window.localStorage.clear();
    mocks.get.mockReset();
  });

  afterEach(() => {
    cleanup();
    window.localStorage.clear();
  });

  it("replaces default wording with administrator saved content", async () => {
    mocks.get.mockResolvedValue({
      footer: { name: "Stored footer" },
      roles: { title: "Stored role title" },
    });

    render(<SiteContentProvider><Consumer /></SiteContentProvider>);
    expect(screen.getByText(/KLB Digital Learning Ecosystem/)).toBeTruthy();

    expect(await screen.findByText("Stored footer|Stored role title")).toBeTruthy();
    expect(mocks.get).toHaveBeenCalledWith("/theming/site-content/");
  });

  it("keeps cached wording when the API request fails", async () => {
    window.localStorage.setItem("klb_site_content", JSON.stringify({
      footer: { name: "Cached footer" },
      roles: { title: "Cached role title" },
    }));
    mocks.get.mockRejectedValue(new Error("request failed"));

    render(<SiteContentProvider><Consumer /></SiteContentProvider>);
    expect(await screen.findByText("Cached footer|Cached role title")).toBeTruthy();
  });
});
