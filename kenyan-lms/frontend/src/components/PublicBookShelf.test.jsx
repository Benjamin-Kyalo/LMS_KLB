import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";

const mocks = vi.hoisted(() => ({
  path: "",
  options: null,
  results: [],
  count: 0,
  reload: vi.fn(),
  setQuery: vi.fn(),
  setPage: vi.fn(),
}));

vi.mock("../hooks/useApi", () => ({
  usePagedResource: (path, options) => {
    mocks.path = path;
    mocks.options = options;
    return {
      data: { results: mocks.results, count: mocks.count },
      results: mocks.results,
      count: mocks.count,
      loading: false,
      error: null,
      page: 1,
      setPage: mocks.setPage,
      query: "",
      setQuery: mocks.setQuery,
      sort: "title",
      setSort: vi.fn(),
      filters: {},
      setFilters: vi.fn(),
      setFilter: vi.fn(),
      reload: mocks.reload,
    };
  },
}));

import PublicBookShelf from "./PublicBookShelf";

describe("public book shelf", () => {
  afterEach(() => {
    cleanup();
    mocks.results = [];
    mocks.count = 0;
    vi.clearAllMocks();
  });

  it("shows published book metadata from the anonymous catalogue", () => {
    mocks.results = [{
      id: 3,
      title: "Grade 4 Mathematics",
      subtitle: "Learner book",
      publisher_name: "KLB",
      subject_name: "Mathematics",
      level_name: "Grade 4",
      chapter_count: 12,
      access_label: "School access",
      description: "A sample catalogue title for the public library.",
    }];
    mocks.count = 1;

    render(<PublicBookShelf title="Books to explore" description="Catalogue preview" />);

    expect(mocks.path).toBe("/content/public/books/");
    expect(mocks.options).toMatchObject({ pageSize: 12, sort: "title" });
    expect(screen.getByRole("heading", { name: "Books to explore" })).toBeTruthy();
    expect(screen.getByText("Grade 4 Mathematics")).toBeTruthy();
    expect(screen.getByText("Grade 4 · Mathematics · KLB")).toBeTruthy();
    expect(screen.getAllByText("School access").length).toBeGreaterThan(0);
    expect(screen.getByText(/12 chapters in this preview/)).toBeTruthy();
  });

  it("offers a clear empty state and a working search", () => {
    render(<PublicBookShelf title="Books to explore" />);

    expect(screen.getByText("No books found")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Search books"), {
      target: { value: "fractions" },
    });
    expect(mocks.setQuery).toHaveBeenCalledWith("fractions");
  });
});
