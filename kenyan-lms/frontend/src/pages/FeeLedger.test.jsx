import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import FeeLedger from "./FeeLedger";

const mocks = vi.hoisted(() => ({
  api: { get: vi.fn(), post: vi.fn(async () => ({})) },
  push: vi.fn(),
  reloadSummary: vi.fn(),
  reloadExceptions: vi.fn(),
  reloadPayments: vi.fn(),
  exception: {
    payment_id: 4, reference: "REC-1", learner_name: "Faith Otieno", amount: "500.00",
    method: "Mobile money", transaction_reference: "", reason: "MISSING_TRANSACTION_REFERENCE",
  },
  payment: {
    id: 4, reference: "REC-1", invoice_reference: "INV-1", amount: "500.00",
    method: "MOBILE", reconciliation_status: "EXCEPTION", paid_at: "2026-11-20T10:00:00Z",
  },
  receipt: {
    receipt_number: "REC-1", school_name: "Receipt School", school_code: "RECP",
    learner_name: "Faith Otieno", admission_number: "ADM-100", invoice_reference: "INV-1",
    fee_name: "Term 1 fees", amount: "500.00", method: "Mobile money",
    transaction_reference: "", payer_phone: "0712345678", recorded_by_name: "Mary Admin",
    reconciliation_status: "Exception", paid_at: "2026-11-20T10:00:00Z",
  },
}));

vi.mock("../services/api", () => ({ api: mocks.api }));
vi.mock("../context/ToastContext", () => ({ useToast: () => ({ push: mocks.push }) }));
vi.mock("../hooks/useApi", () => ({
  useResource: (path) => ({
    data: path.includes("reconciliation")
      ? { exceptions: [mocks.exception], counts: { missing_reference: 1 } }
      : { invoices: 1, amount_due: "1200", amount_paid: "500", balance: "700" },
    loading: false,
    error: null,
    reload: path.includes("reconciliation") ? mocks.reloadExceptions : mocks.reloadSummary,
  }),
  useList: () => ({
    data: [mocks.payment], loading: false, error: null, reload: mocks.reloadPayments,
  }),
}));

function renderPage() {
  return render(<MemoryRouter><FeeLedger /></MemoryRouter>);
}

describe("fee ledger", () => {
  afterEach(() => {
    cleanup();
    mocks.api.get.mockReset();
    mocks.api.post.mockClear();
    mocks.push.mockClear();
    mocks.reloadExceptions.mockClear();
    mocks.reloadPayments.mockClear();
  });

  it("opens a printable receipt derived from a recorded payment", async () => {
    const user = userEvent.setup();
    mocks.api.get.mockResolvedValue(mocks.receipt);
    renderPage();

    await user.click(screen.getByRole("button", { name: "View receipt REC-1" }));

    await waitFor(() => expect(mocks.api.get).toHaveBeenCalledWith("/fees/payments/4/receipt/"));
    const dialog = screen.getByRole("dialog");
    expect(within(dialog).getByText("REC-1")).toBeTruthy();
    expect(within(dialog).getByRole("button", { name: "Print receipt" })).toBeTruthy();
  });

  it("reconciles an exception only after a transaction code is entered", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole("button", { name: "Reconcile receipt REC-1" }));
    const dialog = screen.getByRole("dialog");
    await user.type(within(dialog).getByRole("textbox", { name: "Transaction code" }), "MPESA123");
    await user.click(within(dialog).getByRole("button", { name: "Confirm reconciliation" }));

    await waitFor(() => expect(mocks.api.post).toHaveBeenCalledWith(
      "/fees/payments/4/reconcile/",
      { transaction_reference: "MPESA123", notes: "" },
    ));
    expect(mocks.push).toHaveBeenCalledWith("Payment reconciled and receipt updated.", "success");
    expect(mocks.reloadExceptions).toHaveBeenCalled();
  });
});
