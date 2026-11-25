import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import ResourcePage from "./ResourcePage";
import { api } from "../services/api";

vi.mock("../context/ToastContext", () => ({ useToast: () => ({ push: vi.fn() }) }));
vi.mock("../services/api", () => ({
  api: { post: vi.fn(), patch: vi.fn(), del: vi.fn(), upload: vi.fn(async () => ({})) },
  listAll: vi.fn(async () => []),
}));

const rows = Array.from({ length: 12 }, (_, index) => ({ id: index + 1, name: `Record ${index + 1}` }));

vi.mock("../hooks/useApi", () => ({
  useList: () => ({ data: rows, loading: false, error: null, reload: vi.fn() }),
}));

describe("ResourcePage data tools", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

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

    fireEvent.click(screen.getByRole("button", { name: "Next page" }));
    expect(screen.getByText("Record 11")).toBeTruthy();
    expect(screen.getByText("Page 2 of 2")).toBeTruthy();

    fireEvent.change(screen.getByPlaceholderText("Search all displayed fields"), { target: { value: "Record 3" } });
    expect(screen.getByText("Record 3")).toBeTruthy();
    expect(screen.getByText("1 record")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Next page" })).toBeNull();
  });

  it("sends selected files through the direct upload path", async () => {
    const file = new File(["notes"], "notes.pdf", { type: "application/pdf" });
    render(
      <ResourcePage
        title="Resources"
        endpoint="/content/resources/"
        columns={[{ key: "name", label: "Name" }]}
        fields={[
          { name: "title", label: "Resource title", required: true },
          { name: "file", label: "Upload file", type: "file", accept: ".pdf" },
          { name: "external_url", label: "External URL", showWhen: (form) => form.title === "link" },
        ]}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: "New" }));
    fireEvent.change(screen.getByLabelText("Resource title"), { target: { value: "Revision notes" } });
    fireEvent.change(screen.getByLabelText("Upload file"), { target: { files: [file] } });
    expect(screen.queryByLabelText("External URL")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(api.upload).toHaveBeenCalledTimes(1));
    expect(api.post).not.toHaveBeenCalled();
    const [path, formData, method] = api.upload.mock.calls[0];
    expect(path).toBe("/content/resources/");
    expect(method).toBe("POST");
    expect(formData.get("title")).toBe("Revision notes");
    expect(formData.get("file")).toBe(file);
    expect(formData.has("external_url")).toBe(false);
  });
});
