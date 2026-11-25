import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import Roles from "./Roles";

const mocks = vi.hoisted(() => ({
  post: vi.fn(async () => ({})),
  patch: vi.fn(async () => ({})),
  del: vi.fn(async () => ({})),
  reload: vi.fn(),
  reloadUsers: vi.fn(),
  push: vi.fn(),
  customRoles: [{
    id: 4,
    name: "Office manager",
    description: "Manages office records",
    permissions: ["admin.access", "users.manage"],
    institution: 2,
    is_active: true,
  }],
  users: [{ id: 9, role: "CUSTOM", custom_role: 4, custom_role_name: "Office manager" }],
}));

vi.mock("../services/api", () => ({
  api: { post: mocks.post, patch: mocks.patch, del: mocks.del },
}));
vi.mock("../hooks/useApi", () => ({
  useList: (path) => (path === "/auth/roles/"
    ? { data: mocks.customRoles, loading: false, error: null, reload: mocks.reload }
    : { data: mocks.users, loading: false, error: null, reload: mocks.reloadUsers }),
}));
vi.mock("../context/ToastContext", () => ({ useToast: () => ({ push: mocks.push }) }));

describe("Roles custom role manager", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("lists built-in roles and custom roles with their capabilities", () => {
    render(<Roles />);
    expect(screen.getByRole("heading", { name: "Roles" })).toBeTruthy();
    expect(screen.getByText("Office manager")).toBeTruthy();
    expect(screen.getByText("Admin portal access, Manage users")).toBeTruthy();
    expect(screen.getByText("All capabilities")).toBeTruthy();
    expect(screen.queryByText(/application constants/)).toBeNull();
  });

  it("creates a custom role with a grouped permission picker", async () => {
    render(<Roles />);
    fireEvent.click(screen.getByRole("button", { name: "New custom role" }));

    fireEvent.change(screen.getByLabelText("Role name"), { target: { value: "Report viewer" } });
    fireEvent.change(screen.getByLabelText("Description"), { target: { value: "Reads reports" } });
    fireEvent.click(screen.getByLabelText("Admin portal access"));
    fireEvent.click(screen.getByLabelText("Manage users"));
    expect(screen.getByText(/2 selected: Admin portal access, Manage users/)).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Create role" }));
    await waitFor(() => expect(mocks.post).toHaveBeenCalledWith("/auth/roles/", {
      name: "Report viewer",
      description: "Reads reports",
      permissions: ["admin.access", "users.manage"],
      is_active: true,
    }));
    expect(mocks.reload).toHaveBeenCalled();
  });

  it("edits an existing custom role and its permissions", async () => {
    render(<Roles />);
    fireEvent.click(screen.getByRole("button", { name: "Edit Office manager" }));

    fireEvent.change(screen.getByLabelText("Role name"), { target: { value: "Office lead" } });
    fireEvent.click(screen.getByLabelText("Manage users"));
    fireEvent.click(screen.getByRole("button", { name: "Save role" }));

    await waitFor(() => expect(mocks.patch).toHaveBeenCalledWith("/auth/roles/4/", {
      name: "Office lead",
      description: "Manages office records",
      permissions: ["admin.access"],
      is_active: true,
    }));
  });

  it("deletes a custom role", async () => {
    render(<Roles />);
    fireEvent.click(screen.getByRole("button", { name: "Delete Office manager" }));
    await waitFor(() => expect(mocks.del).toHaveBeenCalledWith("/auth/roles/4/"));
  });
});
