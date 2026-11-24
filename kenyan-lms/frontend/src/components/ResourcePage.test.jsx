import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import ResourcePage from "./ResourcePage";

vi.mock("../context/ToastContext", () => ({ useToast: () => ({ push: vi.fn() }) }));
vi.mock("../services/api", () => ({
  api: { post: vi.fn(), patch: vi.fn(), del: vi.fn() },
  listAll: vi.fn(async () => []),
}));

const rows = Array.from({ length: 12 }, (_, index) => ({ id: index + 1, name: `Record ${index + 1}` }));

vi.mock("../hooks/useApi", () => ({
  useList: () => ({ data: rows, loading: false, error: null, reload: vi.fn() }),
}));

describe("ResourcePage data tools", () => {
  afterEach(cleanup);

  it("paginates long lists and resets to page one when searching", () => {
    render(
      <ResourcePage
        title="Records"
        endpoint="/demo/"
        columns={[{ key: "name", label: "Name" }]}
        fields={[{ name: "name", label: "Name" }]}
      />
    );

    expect(screen.getByText("Page 1 of 2")).toBeTruthy();
    expect(screen.queryByText("Record 11")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(screen.getByText("Record 11")).toBeTruthy();
    expect(screen.getByText("Page 2 of 2")).toBeTruthy();

    fireEvent.change(screen.getByPlaceholderText("Search all displayed fields"), { target: { value: "Record 3" } });
    expect(screen.getByText("Record 3")).toBeTruthy();
    expect(screen.getByText("1 record")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Next" })).toBeNull();
  });
});
