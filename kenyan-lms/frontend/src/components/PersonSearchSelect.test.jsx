import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import PersonSearchSelect from "./PersonSearchSelect";

vi.mock("../services/api", () => ({ api: { get: vi.fn() } }));

import { api } from "../services/api";

const guardian = {
  id: 12,
  guardian_name: "Mary Wambui",
  username: "mary_wambui",
  guardian_number: "GD_MDSCH_2026/11_001",
  phone: "0700000001",
  email: "mary@example.com",
  relationship_to_learner: "Mother",
};

const props = {
  label: "Guardian",
  endpoint: "/guardians/",
  placeholder: "Type a name",
  hint: "Matches load as you type.",
  nameKey: "guardian_name",
  identifierKey: "guardian_number",
  identifierLabel: "Guardian number",
  extraDetails: [{ label: "Phone", key: "phone" }],
};

describe("PersonSearchSelect", () => {
  beforeEach(() => {
    api.get.mockReset();
    api.get.mockResolvedValue({ results: [guardian] });
  });

  afterEach(() => cleanup());

  it("searches the API as the user types and prefills the selected person", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(<PersonSearchSelect {...props} selected={null} onSelect={onSelect} />);

    await user.type(screen.getByRole("combobox"), "mary");
    await waitFor(() => expect(api.get).toHaveBeenCalledWith("/guardians/?search=mary"));
    expect(await screen.findByRole("option")).toBeTruthy();

    await user.click(screen.getByRole("option"));
    expect(onSelect).toHaveBeenCalledWith(guardian);
  });

  it("shows the selected guardian's identifying details", () => {
    render(<PersonSearchSelect {...props} selected={guardian} onSelect={vi.fn()} />);
    expect(screen.getByText("Selected guardian")).toBeTruthy();
    expect(screen.getByText("Mary Wambui")).toBeTruthy();
    expect(screen.getByText("GD_MDSCH_2026/11_001")).toBeTruthy();
    expect(screen.getByText("0700000001")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Change guardian" })).toBeTruthy();
  });

  it("auto-selects an exact identifier without needing a click", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(<PersonSearchSelect {...props} selected={null} onSelect={onSelect} />);

    await user.type(screen.getByRole("combobox"), "GD_MDSCH_2026/11_001");
    await waitFor(() => expect(onSelect).toHaveBeenCalledWith(guardian));
  });

  it("supports keyboard selection", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(<PersonSearchSelect {...props} selected={null} onSelect={onSelect} />);

    await user.type(screen.getByRole("combobox"), "wambui");
    await screen.findByRole("option");
    await user.keyboard("{ArrowDown}{Enter}");
    expect(onSelect).toHaveBeenCalledWith(guardian);
  });

  it("shows a professional message when search fails", async () => {
    api.get.mockRejectedValueOnce(new Error("Network unavailable"));
    const user = userEvent.setup();
    render(<PersonSearchSelect {...props} selected={null} onSelect={vi.fn()} />);

    await user.type(screen.getByRole("combobox"), "mary");
    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(screen.getByRole("alert").textContent).toContain("Network unavailable");
  });
});
