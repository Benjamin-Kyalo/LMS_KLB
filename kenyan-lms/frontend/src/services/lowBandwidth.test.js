import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  clearCache, clearConflicts, enqueueWrite, flushOutbox, isCacheable,
  listConflicts, listOutbox, readCached, setClientConfig, writeCached,
} from "./lowBandwidth";

function storageStub() {
  const values = new Map();
  return {
    getItem: (key) => (values.has(key) ? values.get(key) : null),
    setItem: (key, value) => values.set(key, String(value)),
    removeItem: (key) => values.delete(key),
    clear: () => values.clear(),
    _values: values,
  };
}

const config = {
  version: "test-1",
  offline: {
    enabled: true,
    read_cache: {
      enabled: true,
      paths: ["/api/theming/site-content/"],
      max_age_seconds: 3600,
      max_items: 5,
    },
    outbox: {
      enabled: true,
      methods: ["PATCH", "DELETE"],
      paths: ["/api/theming/site-content/"],
      max_items: 5,
    },
  },
};

describe("low-bandwidth service", () => {
  let store;

  beforeEach(() => {
    store = storageStub();
    vi.stubGlobal("localStorage", store);
    setClientConfig(config);
    clearCache();
    clearConflicts();
    Object.defineProperty(window.navigator, "onLine", {
      configurable: true, value: true,
    });
  });

  afterEach(() => {
    setClientConfig(null);
    vi.unstubAllGlobals();
  });

  it("caches only allowlisted public reads", () => {
    expect(isCacheable("/theming/site-content/")).toBe(true);
    expect(isCacheable("/learners/")).toBe(false);
    expect(writeCached("/learners/", [{ id: 1, learner_name: "Amina" }])).toBe(false);

    const payload = { app: { adminBrand: "School" }, updated_at: "2026-11-26T10:00:00+00:00" };
    expect(writeCached("/theming/site-content/", payload)).toBe(true);
    expect(readCached("/theming/site-content/")?.data).toEqual(payload);
    expect(JSON.stringify([...store._values.values()])).not.toContain("Amina");
  });

  it("refuses to queue person-like or credential-like fields", () => {
    expect(() => enqueueWrite({
      method: "PATCH",
      path: "/theming/site-content/",
      body: { email: "someone@example.com" },
    })).toThrow(/personal or credential/i);

    expect(() => enqueueWrite({
      method: "PATCH",
      path: "/theming/site-content/",
      body: { content: { token: "abc" } },
    })).toThrow(/personal or credential/i);

    expect(listOutbox()).toHaveLength(0);
    const item = enqueueWrite({
      method: "PATCH",
      path: "/api/theming/site-content/",
      body: { content: { app: { adminBrand: "School" } } },
      ifMatch: "2026-11-26T10:00:00+00:00",
    });
    expect(item?.path).toBe("/theming/site-content/");
    expect(listOutbox()).toHaveLength(1);
    expect(JSON.stringify([...store._values.values()])).not.toContain("csrftoken");
  });

  it("turns a 409 replay into a conflict without keeping the request body", async () => {
    enqueueWrite({
      method: "PATCH",
      path: "/theming/site-content/",
      body: { content: { app: { adminBrand: "School" } } },
    });
    const send = vi.fn(async () => {
      throw {
        status: 409,
        message: "This record changed since you loaded it.",
        details: { server: { id: 1, updated_at: "2026-11-26T11:00:00+00:00" } },
      };
    });

    const result = await flushOutbox(send);
    expect(result).toMatchObject({ sent: 0, conflicts: 1, kept: 0 });
    expect(listOutbox()).toHaveLength(0);
    expect(listConflicts()[0]).toMatchObject({
      path: "/theming/site-content/",
      server_updated_at: "2026-11-26T11:00:00+00:00",
    });
    expect(JSON.stringify(listConflicts())).not.toContain("adminBrand");
  });
});
