import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Library from "./Library";

const mocks = vi.hoisted(() => ({
  reload: vi.fn(async () => {}),
  setQuery: vi.fn(),
  setSort: vi.fn(),
  setPage: vi.fn(),
  setFilter: vi.fn(),
  setFilters: vi.fn(),
}));

vi.mock("../hooks/useApi", () => ({
  usePagedResource: () => ({
    data: [], results: [], loading: false, error: null, count: 0,
    page: 1, query: "", sort: "title", filters: {},
    reload: mocks.reload, setQuery: mocks.setQuery, setSort: mocks.setSort,
    setPage: mocks.setPage, setFilter: mocks.setFilter, setFilters: mocks.setFilters,
  }),
  useResource: () => ({ data: {}, loading: false, error: null, reload: mocks.reload }),
}));

describe("public library", () => {
  afterEach(() => {
    cleanup();
    delete window.__KLB_SITE_CONFIG__;
  });

  it("renders the managed library guide alongside the catalogue components", () => {
    const { container } = render(<MemoryRouter><Library /></MemoryRouter>);

    expect(screen.getByRole("heading", { level: 1, name: "The KLB Digital Library" }))
      .toBeTruthy();
    expect(screen.getByRole("heading", { name: "Find the next resource that makes a difference." }))
      .toBeTruthy();
    expect(screen.getByText(
      "Explore a growing collection of available educational publications and learning resources from KLB and other approved content providers.",
    )).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Library categories" })).toBeTruthy();
    expect(screen.getByText("Textbooks")).toBeTruthy();
    expect(screen.getByText("Assessment resources")).toBeTruthy();
    expect(screen.getByText("Search by book title, subject, grade or keyword...")).toBeTruthy();
    expect(screen.getByText("Education level")).toBeTruthy();
    expect(screen.getByText("Access availability")).toBeTruthy();
    expect(screen.getByText("Included in your subscription")).toBeTruthy();
    expect(screen.getByText("Not currently available")).toBeTruthy();

    // Implementer-only pricing guidance must never be shown to visitors.
    expect(screen.queryByText(/Do not display a purchase price/)).toBeNull();

    // Both catalogue components remain in place.
    expect(screen.getByRole("heading", { name: "Books to explore" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Find learning resources" })).toBeTruthy();
    expect(container.querySelector(".resource-filters")).toBeTruthy();
  });

  it("renders managed library copy from a runtime override", () => {
    window.__KLB_SITE_CONFIG__ = {
      content: {
        publicPages: {
          library: {
            pageTitle: "Custom library title",
            title: "Custom library introduction",
            categoriesTitle: "Custom categories",
            categories: ["Custom category"],
            searchPlaceholder: "Custom search hint",
            filters: ["Custom filter"],
            accessLabels: ["Custom access label"],
          },
        },
      },
    };
    render(<MemoryRouter><Library /></MemoryRouter>);

    expect(screen.getByRole("heading", { level: 1, name: "Custom library title" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Custom library introduction" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Custom categories" })).toBeTruthy();
    expect(screen.getByText("Custom category")).toBeTruthy();
    expect(screen.getByText("Custom search hint")).toBeTruthy();
    expect(screen.getByText("Custom filter")).toBeTruthy();
    expect(screen.getByText("Custom access label")).toBeTruthy();
    expect(screen.queryByText("Textbooks")).toBeNull();
  });
});
