import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import SchoolProfile from "./SchoolProfile";

const school = {
  id: 4,
  name: "Mwangaza Secondary",
  code: "MWANG-001",
  institution_type_name: "Secondary",
  county: "Machakos",
  phone: "0201234567",
  email: "office@mwangaza.example",
  website: "https://mwangaza.example",
  motto: "Learn with purpose",
  address_line: "PO Box 10, Machakos",
  logo: null,
};

const mocks = vi.hoisted(() => ({
  patch: vi.fn(async () => ({})),
  upload: vi.fn(async () => ({})),
  get: vi.fn(async () => ({ id: 1, role: "SCHOOL_ADMIN" })),
  reload: vi.fn(),
  push: vi.fn(),
}));

vi.mock("../services/api", () => ({
  api: { patch: mocks.patch, upload: mocks.upload, get: mocks.get },
}));
vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({ user: { id: 1, role: "SCHOOL_ADMIN" }, setUser: vi.fn() }),
}));
vi.mock("../context/ToastContext", () => ({
  useToast: () => ({ push: mocks.push }),
}));
vi.mock("../hooks/useApi", () => ({
  useResource: () => ({ data: school, loading: false, error: null, reload: mocks.reload }),
}));

describe("SchoolProfile", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("loads school details and saves edits to the scoped endpoint", async () => {
    render(<SchoolProfile />);
    expect((screen.getByLabelText("Institution name")).value).toBe("Mwangaza Secondary");
    fireEvent.change(screen.getByLabelText("Phone number"), { target: { value: "0700000001" } });
    fireEvent.click(screen.getByRole("button", { name: /Save school details/i }));
    await waitFor(() => expect(mocks.patch).toHaveBeenCalledWith(
      "/institutions/mine/",
      expect.objectContaining({ phone: "0700000001", motto: "Learn with purpose" })
    ));
    expect(mocks.reload).toHaveBeenCalled();
  });

  it("uploads a logo through the file endpoint", async () => {
    render(<SchoolProfile />);
    const file = new File(["logo"], "logo.png", { type: "image/png" });
    fireEvent.change(document.getElementById("school-logo"), { target: { files: [file] } });
    await waitFor(() => expect(mocks.upload).toHaveBeenCalledWith("/institutions/mine/", expect.any(FormData)));
  });
});
