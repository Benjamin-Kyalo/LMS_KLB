import { afterEach, describe, expect, it, vi } from "vitest";
import { act, renderHook, waitFor } from "@testing-library/react";
import { usePagedResource } from "./useApi";
import { api } from "../services/api";

vi.mock("../services/api", () => ({
  api: { get: vi.fn(async () => ({ results: [], count: 0 })) },
  listAll: vi.fn(),
}));

describe("usePagedResource", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("asks the API for paged, filtered, searched and sorted results", async () => {
    api.get.mockResolvedValueOnce({ results: [{ id: 1 }], count: 1, next: null, previous: null });
    const { result } = renderHook(() => usePagedResource("/content/public/resources/", {
      pageSize: 12,
      filters: { level: "2" },
    }));

    await waitFor(() => expect(result.current.results).toEqual([{ id: 1 }]));
    const path = api.get.mock.calls[0][0];
    expect(path).toContain("/content/public/resources/?");
    expect(path).toContain("page=1");
    expect(path).toContain("page_size=12");
    expect(path).toContain("level=2");
    expect(path).toContain("ordering=title");

    act(() => result.current.setFilter("area", "5"));
    await waitFor(() => expect(api.get.mock.calls[1][0]).toContain("area=5"));
    expect(api.get.mock.calls[1][0]).toContain("level=2");

    act(() => result.current.setQuery("fraction"));
    await waitFor(() => expect(api.get.mock.calls[2][0]).toContain("q=fraction"));
    expect(api.get.mock.calls[2][0]).toContain("page=1");
  });
});
