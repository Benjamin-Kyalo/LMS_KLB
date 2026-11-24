import { beforeEach, describe, expect, it } from "vitest";
import { all, clear, count, enqueue, remove, update } from "./offlineQueue";

describe("offline mutation queue", () => {
  beforeEach(async () => { await clear(); });

  it("enqueues a mutation with useful metadata", async () => {
    const item = await enqueue({ path: "/learners/", method: "POST", body: { admission_number: "ADM9" } });
    expect(item.id).toBeGreaterThan(0);
    expect(item.attempts).toBe(0);
    expect(item.lastError).toBeNull();
    expect(await count()).toBe(1);
    const rows = await all();
    expect(rows[0].path).toBe("/learners/");
    expect(rows[0].body.admission_number).toBe("ADM9");
  });

  it("records server rejections without losing the change", async () => {
    const item = await enqueue({ path: "/learners/", method: "POST", body: {} });
    await update(item.id, { attempts: 1, lastError: "HTTP 400: invalid" });
    const [row] = await all();
    expect(row.attempts).toBe(1);
    expect(row.lastError).toContain("HTTP 400");
    expect(await count()).toBe(1);
  });

  it("removes and clears entries", async () => {
    const a = await enqueue({ path: "/a/", method: "POST", body: {} });
    await enqueue({ path: "/b/", method: "PATCH", body: {} });
    await remove(a.id);
    expect(await count()).toBe(1);
    await clear();
    expect(await count()).toBe(0);
  });
});
