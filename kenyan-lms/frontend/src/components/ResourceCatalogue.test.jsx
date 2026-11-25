import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import ResourceCard from "./ResourceCard";
import ResourceCatalogue from "./ResourceCatalogue";
import ResourceDetail from "./ResourceDetail";
import ResourceFilters from "./ResourceFilters";
import { api } from "../services/api";

const hookMocks = vi.hoisted(() => ({
  setFilter: vi.fn(),
  setFilters: vi.fn(),
  setQuery: vi.fn(),
  setSort: vi.fn(),
  reload: vi.fn(),
}));

vi.mock("../services/api", () => ({
  api: { download: vi.fn(async () => {}) },
}));

vi.mock("../hooks/useApi", () => ({
  useResource: () => ({
    data: {
      levels: [{
        id: 3,
        name: "Grade 4",
        learning_areas: [{ id: 5, name: "Mathematics" }],
      }],
      learning_areas: [{ id: 5, name: "Mathematics" }],
    },
    error: null,
  }),
  usePagedResource: () => ({
    data: { results: [], count: 0 },
    results: [],
    count: 0,
    loading: false,
    error: null,
    page: 1,
    setPage: vi.fn(),
    query: "",
    setQuery: hookMocks.setQuery,
    sort: "title",
    setSort: hookMocks.setSort,
    filters: {},
    setFilters: hookMocks.setFilters,
    setFilter: hookMocks.setFilter,
    reload: hookMocks.reload,
  }),
}));

describe("resource catalogue presentation", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("collects public and portal filter parameters", () => {
    const onFilter = vi.fn();
    const onQuery = vi.fn();
    render(
      <ResourceFilters
        facets={{
          levels: [{ id: 1, name: "Grade 4", learning_areas: [{ id: 5, name: "Mathematics" }] }],
          collections: [{ id: 2, name: "Revision" }],
          subjects: [{ id: 7, name: "Maths" }],
          classes: [{ id: 9, name: "Grade 4", stream: "East" }],
        }}
        filters={{ level: "1" }}
        onFilter={onFilter}
        onQuery={onQuery}
      />
    );

    fireEvent.change(screen.getByLabelText("Learning area"), { target: { value: "5" } });
    expect(onFilter).toHaveBeenCalledWith("area", "5");
    fireEvent.change(screen.getByLabelText("Search resources"), { target: { value: "fractions" } });
    expect(onQuery).toHaveBeenCalledWith("fractions");
    expect(screen.getByLabelText("Subject")).toBeTruthy();
    expect(screen.getByLabelText("Class")).toBeTruthy();
  });

  it("sends friendly level and area filters using API field names", () => {
    render(<ResourceCatalogue endpoint="/content/public/resources/" title="Resources" />);

    fireEvent.change(screen.getByLabelText("Level"), { target: { value: "3" } });
    expect(hookMocks.setFilters).toHaveBeenCalledTimes(1);
    const update = hookMocks.setFilters.mock.calls[0][0];
    expect(update({ resource_type: "PDF" })).toEqual({
      resource_type: "PDF",
      education_level: "3",
      learning_area: "",
    });

    fireEvent.change(screen.getByLabelText("Learning area"), { target: { value: "5" } });
    expect(hookMocks.setFilter).toHaveBeenCalledWith("learning_area", "5");
  });

  it("shows a card summary and delegates selection", () => {
    const onSelect = vi.fn();
    render(
      <ResourceCard
        resource={{
          id: 1, title: "Fraction guide", resource_type: "PDF", offline_available: true,
          education_level_name: "Grade 4", learning_area_name: "Mathematics",
          description: "Worked examples for beginner fractions.",
        }}
        onSelect={onSelect}
      />
    );
    expect(screen.getByText("Grade 4 · Mathematics")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "View Fraction guide details" }));
    expect(onSelect).toHaveBeenCalledWith(expect.objectContaining({ id: 1 }));
  });

  it("renders only server-built embeds in a sandboxed frame", () => {
    render(
      <ResourceDetail
        resource={{
          id: 1, title: "Counting video", resource_type: "VIDEO",
          embed_url: "https://www.youtube.com/embed/abc123",
          external_url: "<script>alert(1)</script>",
        }}
        onClose={vi.fn()}
      />
    );
    const iframe = document.querySelector("iframe");
    expect(iframe.getAttribute("src")).toBe("https://www.youtube.com/embed/abc123");
    expect(iframe.getAttribute("sandbox")).toContain("allow-scripts");
    expect(iframe.getAttribute("referrerpolicy")).toBe("no-referrer");
    expect(document.querySelector("script")).toBeNull();
  });

  it("downloads local files through the authenticated download endpoint", async () => {
    render(
      <ResourceDetail
        resource={{
          id: 4, title: "Notes", resource_type: "PDF", file_available: true,
          download_url: "/content/resources/4/download/",
        }}
        onClose={vi.fn()}
      />
    );
    fireEvent.click(screen.getByRole("button", { name: "Download Notes file" }));
    await waitFor(() => expect(api.download).toHaveBeenCalledWith(
      "/content/resources/4/download/", "Notes.pdf",
    ));
  });
});
