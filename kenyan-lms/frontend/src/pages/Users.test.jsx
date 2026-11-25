import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import Users from "./Users";

const mocks = vi.hoisted(() => ({
  actor: { id: 1, role: "ADMIN", institution_id: 2 },
  post: vi.fn(async () => ({})),
  patch: vi.fn(async () => ({})),
  del: vi.fn(async () => ({})),
  reload: vi.fn(),
  reloadRoles: vi.fn(),
  listAll: vi.fn(async () => [{ id: 2, name: "Main school" }]),
  push: vi.fn(),
  users: [{
    id: 5,
    username: "officer",
    full_name: "Amina Yusuf",
    role: "CUSTOM",
    custom_role: 4,
    custom_role_name: "Office manager",
    is_active: true,
  }],
  roleOptions: [
    { value: "SUPER_ADMIN", label: "Platform Super Administrator", kind: "builtin" },
    { value: "ADMIN", label: "Administrator", kind: "builtin" },
    { value: "LEARNER", label: "Learner", kind: "builtin" },
    {
      value: "CUSTOM",
      label: "Office manager",
      kind: "custom",
      custom_role: 4,
      capabilities: ["admin.access", "users.manage"],
    },
  ],
}));

vi.mock("../context/AuthContext", () => ({ useAuth: () => ({ user: mocks.actor }) }));
vi.mock("../services/api", () => ({
  api: { post: mocks.post, patch: mocks.patch, del: mocks.del },
  listAll: mocks.listAll,
}));
vi.mock("../hooks/useApi", () => ({
  useList: (path) => (path === "/auth/users/roles/"
    ? { data: mocks.roleOptions, loading: false, error: null, reload: mocks.reloadRoles }
    : { data: mocks.users, loading: false, error: null, reload: mocks.reload }),
}));
vi.mock("../context/ToastContext", () => ({ useToast: () => ({ push: mocks.push }) }));

function fillUserForm() {
  fireEvent.change(screen.getByLabelText("Username"), { target: { value: "new.user" } });
  fireEvent.change(screen.getByLabelText("First name"), { target: { value: "New" } });
  fireEvent.change(screen.getByLabelText("Last name"), { target: { value: "User" } });
  fireEvent.change(screen.getByLabelText("Email"), { target: { value: "new@example.invalid" } });
}

describe("Users custom role assignment", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
    mocks.actor = { id: 1, role: "ADMIN", institution_id: 2 };
  });

  it("shows the custom role name and assigns custom_role for CUSTOM", async () => {
    render(<Users />);
    expect(screen.getByRole("cell", { name: "Office manager" })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "New user" }));
    expect(screen.queryByLabelText("Institution")).toBeNull();
    const roleSelect = screen.getByLabelText("Role");
    expect(roleSelect.querySelector('option[value="SUPER_ADMIN"]')).toBeNull();
    expect(within(roleSelect).getByRole("option", { name: "Office manager" })).toBeTruthy();

    fillUserForm();
    fireEvent.change(roleSelect, { target: { value: "CUSTOM:4" } });
    fireEvent.click(screen.getByRole("button", { name: "Save user" }));

    await waitFor(() => expect(mocks.post).toHaveBeenCalledWith("/auth/users/", expect.objectContaining({
      username: "new.user",
      role: "CUSTOM",
      custom_role: 4,
    })));
    expect(mocks.post.mock.calls[0][1]).not.toHaveProperty("institution");
  });

  it("only offers institution choice to a super admin", async () => {
    mocks.actor = { id: 2, role: "SUPER_ADMIN", institution_id: null };
    render(<Users />);
    fireEvent.click(screen.getByRole("button", { name: "New user" }));

    expect(screen.getByLabelText("Institution")).toBeTruthy();
    await waitFor(() => expect(within(screen.getByLabelText("Institution")).getByRole("option", { name: "Main school" })).toBeTruthy());
    expect(within(screen.getByLabelText("Role")).getByRole("option", { name: "Platform Super Administrator" })).toBeTruthy();
  });
});
