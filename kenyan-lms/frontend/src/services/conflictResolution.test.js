import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ConflictError, conflictCount, resolveConflict, request, syncPending } from "./api";
import { all, clear, enqueue, update } from "./offlineQueue";

function jsonResponse(body, status = 200, statusText = "OK") {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText,
    text: async () => JSON.stringify(body),
  };
}

function conflictResponse(overrides = {}) {
  return jsonResponse({
    detail: "This record changed on the server.",
    code: "conflict",
    server: { id: 7, name: "Server copy" },
    ...overrides,
  }, 409, "Conflict");
}

async function conflictedItem() {
  const item = await enqueue({ path: "/learners/7/", method: "PATCH", body: { name: "Local copy" } });
  await update(item.id, {
    conflict: true,
    conflictDetails: {
      status: 409,
      message: "This record changed on the server.",
      server: { id: 7, name: "Server copy" },
      code: "conflict",
    },
    attempts: 1,
    lastError: "Conflict (HTTP 409): This record changed on the server.",
  });
  return item;
}

describe("offline mutation conflict handling", () => {
  beforeEach(async () => {
    await clear();
    // Mutations only queue while authenticated; keep this local to the test.
    vi.stubGlobal("localStorage", {
      getItem: (key) => (key === "klb_token" ? "test-token" : null),
      setItem: () => {},
      removeItem: () => {},
      clear: () => {},
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("maps an HTTP 409 response to ConflictError with details and the server snapshot", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => conflictResponse()));

    await expect(request("/learners/7/")).rejects.toMatchObject({
      status: 409,
      message: "This record changed on the server.",
    });

    let caught;
    try {
      await request("/learners/7/");
    } catch (err) {
      caught = err;
    }
    expect(caught).toBeInstanceOf(ConflictError);
    expect(caught.details.code).toBe("conflict");
    expect(caught.server).toEqual({ id: 7, name: "Server copy" });
  });

  it("leaves conflicted items queued and reports conflicts from syncPending", async () => {
    const item = await enqueue({ path: "/learners/7/", method: "PATCH", body: { name: "Local copy" } });
    vi.stubGlobal("fetch", vi.fn(async () => conflictResponse()));

    const events = [];
    const onConflict = (event) => events.push(event.detail);
    window.addEventListener("klb:sync-conflict", onConflict);
    try {
      const result = await syncPending();
      expect(result).toEqual({ synced: 0, failed: 0, conflicts: 1, autoResolved: 0 });

      const [row] = await all();
      expect(row.id).toBe(item.id);
      expect(row.conflict).toBe(true);
      expect(row.attempts).toBe(1);
      expect(row.conflictDetails.status).toBe(409);
      expect(row.conflictDetails.code).toBe("conflict");
      expect(row.conflictDetails.server).toEqual({ id: 7, name: "Server copy" });
      expect(row.lastError).toContain("409");
      expect(await conflictCount()).toBe(1);

      expect(events).toHaveLength(1);
      expect(events[0].item.id).toBe(item.id);
      expect(events[0].details).toEqual(row.conflictDetails);
    } finally {
      window.removeEventListener("klb:sync-conflict", onConflict);
    }
  });

  it("automatically rebases a stale update against the current server version", async () => {
    await enqueue({ path: "/learners/7/", method: "PATCH", body: { name: "Local copy" } });
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(conflictResponse({
        server: { id: 7, updated_at: "2026-11-23T10:00:00Z", name: "Server copy" },
      }))
      .mockResolvedValueOnce(jsonResponse({ id: 7, name: "Local copy" }));
    vi.stubGlobal("fetch", fetchMock);

    const events = [];
    const onResolved = (event) => events.push(event.detail);
    window.addEventListener("klb:sync-conflict-resolved", onResolved);
    try {
      const result = await syncPending();
      expect(result).toEqual({ synced: 0, failed: 0, conflicts: 0, autoResolved: 1 });
      expect(await all()).toEqual([]);
      expect(fetchMock).toHaveBeenCalledTimes(2);
      expect(fetchMock.mock.calls[1][1].headers["If-Match"]).toBe("2026-11-23T10:00:00Z");
      expect(events).toEqual([{
        id: expect.any(Number),
        strategy: "rebase",
        ok: true,
        automatic: true,
      }]);
    } finally {
      window.removeEventListener("klb:sync-conflict-resolved", onResolved);
    }
  });

  it("keeps a conflict for manual review when rebase also conflicts", async () => {
    await enqueue({ path: "/learners/7/", method: "PATCH", body: { name: "Local copy" } });
    vi.stubGlobal("fetch", vi.fn(async () => conflictResponse({
      server: { id: 7, updated_at: "2026-11-23T10:00:00Z" },
    })));

    const result = await syncPending();
    expect(result).toEqual({ synced: 0, failed: 0, conflicts: 1, autoResolved: 0 });
    const [row] = await all();
    expect(row.conflict).toBe(true);
    expect(row.lastError).toContain("Automatic rebase failed");
  });

  it("resolveConflict('discard') removes the conflicted item", async () => {
    const item = await conflictedItem();
    const events = [];
    const onResolved = (event) => events.push(event.detail);
    window.addEventListener("klb:sync-conflict-resolved", onResolved);
    try {
      const result = await resolveConflict(item.id, "discard");
      expect(result).toEqual({ ok: true });
      expect(await all()).toEqual([]);
      expect(await conflictCount()).toBe(0);
      expect(events).toEqual([{ id: item.id, strategy: "discard", ok: true }]);
    } finally {
      window.removeEventListener("klb:sync-conflict-resolved", onResolved);
    }
  });

  it("resolveConflict('retry') replays the saved body successfully and removes the item", async () => {
    const item = await conflictedItem();
    const fetchMock = vi.fn(async () => jsonResponse({ ok: true }));
    vi.stubGlobal("fetch", fetchMock);

    const result = await resolveConflict(item.id, "retry");
    expect(result).toEqual({ ok: true });
    expect(await all()).toEqual([]);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/learners/7/");
    expect(options.method).toBe("PATCH");
    expect(JSON.parse(options.body)).toEqual({ name: "Local copy" });
  });

  it("also treats a non-409 body with code='conflict' as a conflict", async () => {
    vi.stubGlobal("fetch", vi.fn(async () =>
      jsonResponse({ detail: "Stale record", code: "conflict" }, 400, "Bad Request")));

    let caught;
    try {
      await request("/learners/7/");
    } catch (err) {
      caught = err;
    }
    expect(caught).toBeInstanceOf(ConflictError);
    expect(caught.status).toBe(400);
  });
});
