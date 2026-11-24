import { afterEach, describe, expect, it, vi } from "vitest";
import { listAll } from "./api";

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
