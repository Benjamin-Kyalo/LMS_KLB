import { afterEach, describe, expect, it, vi } from "vitest";
import { api, listAll, setCsrfToken } from "./api";

describe("listAll pagination", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("follows absolute DRF next links without corrupting the API base", async () => {
    const calls = [];
    vi.stubGlobal("localStorage", {
      getItem: () => null,
      setItem: () => {},
      removeItem: () => {},
      clear: () => {},
    });
    vi.stubGlobal("fetch", vi.fn(async (url) => {
      calls.push(url);
      const body = calls.length === 1
        ? {
            results: [{ id: 1 }],
            next: "http://127.0.0.1:8000/api/assessments/results/?page=2",
          }
        : { results: [{ id: 2 }], next: null };
      return {
        ok: true,
        status: 200,
        statusText: "OK",
        text: async () => JSON.stringify(body),
      };
    }));

    const rows = await listAll("/assessments/results/");

    expect(rows).toEqual([{ id: 1 }, { id: 2 }]);
    expect(calls).toEqual([
      "/api/assessments/results/",
      "/api/assessments/results/?page=2",
    ]);
  });
});

describe("authenticated downloads", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    delete URL.createObjectURL;
    delete URL.revokeObjectURL;
  });

  it("fetches a blob with the session cookie and saves it under the suggested name", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      status: 200,
      text: async () => "",
      blob: async () => new Blob(["file"], { type: "application/pdf" }),
    }));
    vi.stubGlobal("fetch", fetchMock);
    // Keep the real URL constructor so fullUrl() still parses the API base.
    vi.stubGlobal("URL", Object.assign(URL, {
      createObjectURL: vi.fn(() => "blob:test"),
      revokeObjectURL: vi.fn(),
    }));
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});

    await api.download("/content/resources/1/download/", "notes.pdf");

    expect(fetchMock.mock.calls[0][0]).toBe("/api/content/resources/1/download/");
    expect(fetchMock.mock.calls[0][1]).toEqual({ credentials: "include" });
    expect(click).toHaveBeenCalledTimes(1);
    expect(document.querySelector("a[download='notes.pdf']")).toBeNull();
  });

  it("reports HTTP errors without downloading a blob", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => ({
      ok: false,
      status: 403,
      statusText: "Forbidden",
      text: async () => JSON.stringify({ detail: "Not shared with your school." }),
      blob: vi.fn(),
    })));

    await expect(api.download("/content/resources/1/download/"))
      .rejects.toMatchObject({ status: 403, message: "Not shared with your school." });
  });
});

describe("API error messages", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("shows a field-level validation message instead of Bad Request", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => ({
      ok: false,
      status: 400,
      statusText: "Bad Request",
      text: async () => JSON.stringify({
        image: "Use a photo at least 640×360 pixels.",
      }),
    })));

    await expect(api.post("/theming/site-content/image/", {}))
      .rejects.toMatchObject({
        status: 400,
        message: "image: Use a photo at least 640×360 pixels.",
      });
  });
});

describe("session request hardening", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    setCsrfToken("");
  });

  it("includes cookies and a CSRF header only on state-changing requests", async () => {
    setCsrfToken("csrf-123");
    const fetchMock = vi.fn(async () => ({
      ok: true,
      status: 200,
      statusText: "OK",
      text: async () => "",
    }));
    vi.stubGlobal("fetch", fetchMock);

    await api.post("/auth/logout/", {});
    await api.get("/auth/me/");

    expect(fetchMock.mock.calls[0][1].credentials).toBe("include");
    expect(fetchMock.mock.calls[0][1].headers["X-CSRFToken"]).toBe("csrf-123");
    expect(fetchMock.mock.calls[1][1].credentials).toBe("include");
    expect(fetchMock.mock.calls[1][1].headers["X-CSRFToken"]).toBeUndefined();
  });
});
