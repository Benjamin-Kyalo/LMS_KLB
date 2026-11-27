import { afterEach, describe, expect, it, vi } from "vitest";
import { api, listAll, setCsrfToken } from "./api";
import { clearCache, listOutbox, setClientConfig } from "./lowBandwidth";

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

  it("replaces a Django HTML error page with a short professional message", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => ({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
      text: async () => "<!DOCTYPE html><html><body>SessionInterrupted</body></html>",
    })));

    await expect(api.post("/auth/users/99/reset_password/", {}))
      .rejects.toMatchObject({
        status: 500,
        message: "The server could not complete this request. It has been logged. Please try again.",
      });
  });
});

describe("optimistic concurrency and low-bandwidth queue", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    setCsrfToken("");
    setClientConfig(null);
    clearCache();
  });

  it("sends If-Match on PATCH and DELETE without storing it as a secret", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true, status: 200, statusText: "OK", text: async () => "{}",
    }));
    vi.stubGlobal("fetch", fetchMock);
    setCsrfToken("csrf-123");

    await api.patch("/theming/palettes/1/", { name: "New" }, { ifMatch: "2026-11-26T10:00:00+00:00" });
    await api.del("/theming/palettes/1/", { ifMatch: "2026-11-26T10:00:00+00:00" });

    expect(fetchMock.mock.calls[0][1].headers["If-Match"]).toBe("2026-11-26T10:00:00+00:00");
    expect(fetchMock.mock.calls[1][1].headers["If-Match"]).toBe("2026-11-26T10:00:00+00:00");
    expect(fetchMock.mock.calls[0][1].headers["X-CSRFToken"]).toBe("csrf-123");
  });

  it("queues an allowlisted offline PATCH and reports it visibly", async () => {
    const values = new Map();
    vi.stubGlobal("localStorage", {
      getItem: (key) => (values.has(key) ? values.get(key) : null),
      setItem: (key, value) => values.set(key, String(value)),
      removeItem: (key) => values.delete(key),
      clear: () => values.clear(),
    });
    Object.defineProperty(window.navigator, "onLine", { configurable: true, value: false });
    vi.stubGlobal("fetch", vi.fn(async () => { throw new TypeError("network"); }));
    setClientConfig({
      version: "test",
      offline: {
        enabled: true,
        read_cache: { enabled: false, paths: [], max_age_seconds: 1, max_items: 1 },
        outbox: {
          enabled: true, methods: ["PATCH", "DELETE"],
          paths: ["/api/theming/site-content/"], max_items: 5,
        },
      },
    });

    await expect(api.patch("/theming/site-content/", { content: { app: { adminBrand: "School" } } }))
      .rejects.toMatchObject({ status: 0, message: /queued on this device/i, queued: true });
    expect(listOutbox()).toHaveLength(1);
    expect(JSON.stringify([...values.values()])).not.toContain("csrftoken");
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
