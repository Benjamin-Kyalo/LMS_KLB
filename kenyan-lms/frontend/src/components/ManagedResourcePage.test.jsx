import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import ManagedResourcePage from "./ManagedResourcePage";

const mocks = vi.hoisted(() => ({ role: "ADMIN", capabilities: [] }));

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({
    user: { id: 1, role: mocks.role, capabilities: mocks.capabilities, institution_id: 7 },
  }),
}));
vi.mock("../services/api", () => ({
  api: { post: vi.fn(), patch: vi.fn(), del: vi.fn() },
  listAll: vi.fn(async () => []),
}));
vi.mock("../context/ToastContext", () => ({ useToast: () => ({ push: vi.fn() }) }));
vi.mock("../hooks/useApi", () => ({
  useList: () => ({ data: [{ id: 1, name: "Existing" }], loading: false, error: null, reload: vi.fn() }),
}));

const fields = [{ name: "name", label: "Name" }];
const columns = [{ key: "name", label: "Name" }];

function renderPage(endpoint) {
  return render(
    <ManagedResourcePage
      title="Records"
      overline="Test"
      endpoint={endpoint}
      columns={columns}
      fields={fields}
    />
  );
}

describe("ManagedResourcePage action permissions", () => {
  afterEach(() => {
    cleanup();
    mocks.role = "ADMIN";
    mocks.capabilities = [];
  });

  it("lets a school admin write school structure but not the institution list", () => {
    renderPage("/institutions/subjects/");
    expect(screen.getByRole("button", { name: "New" })).toBeTruthy();
    expect(screen.getAllByRole("button", { name: "Edit Existing" }).length).toBeGreaterThan(0);
    cleanup();

    renderPage("/institutions/");
    expect(screen.queryByRole("button", { name: "New" })).toBeNull();
  });

  it("hides write actions from a teacher on admin-only records", () => {
    mocks.role = "TEACHER";
    renderPage("/institutions/subjects/");
    expect(screen.queryByRole("button", { name: "New" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Edit Existing" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Delete Existing" })).toBeNull();
    expect(screen.getByRole("button", { name: "View Existing" })).toBeTruthy();
  });

  it("still lets a teacher write teaching records", () => {
    mocks.role = "TEACHER";
    renderPage("/assessments/exams/");
    expect(screen.getByRole("button", { name: "New" })).toBeTruthy();
  });

  it("lets a custom content role write publishing records only", () => {
    mocks.role = "CUSTOM";
    mocks.capabilities = ["admin.access", "content.manage"];
    renderPage("/content/resources/");
    expect(screen.getByRole("button", { name: "New" })).toBeTruthy();
    cleanup();

    renderPage("/institutions/subjects/");
    expect(screen.queryByRole("button", { name: "New" })).toBeNull();
  });

  it("keeps learner submissions read-only in the staff screen", () => {
    renderPage("/courses/submissions/");
    expect(screen.queryByRole("button", { name: "New" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Edit Existing" })).toBeNull();
  });

  it("fails closed for an endpoint with no known write scope", () => {
    renderPage("/unknown/resource/");
    expect(screen.queryByRole("button", { name: "New" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Delete Existing" })).toBeNull();
    expect(screen.getByRole("button", { name: "View Existing" })).toBeTruthy();
  });
});
