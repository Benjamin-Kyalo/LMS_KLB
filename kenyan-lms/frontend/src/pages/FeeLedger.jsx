import { useState } from "react";
import { Link } from "react-router-dom";
import { useToast } from "../context/ToastContext";
import { useList, useResource } from "../hooks/useApi";
import { api } from "../services/api";
import useTableControls from "../hooks/useTableControls";
import DataTable from "../components/DataTable";
import FormField from "../components/FormField";
import Modal from "../components/Modal";
import RollingLabel from "../components/RollingLabel";
import StatCard from "../components/StatCard";
import { TableToolbar, TablePagination } from "../components/TableTools";
import { formatDateTime } from "../utilities/format";

const money = (value) => (value === null || value === undefined ? "—" : `KES ${Number(value).toLocaleString("en-KE")}`);

export default function FeeLedger() {
  const { push } = useToast();
  const summary = useResource("/fees/invoices/summary/");
  const exceptions = useResource("/fees/reconciliation/");
  const payments = useList("/fees/payments/");
  const exceptionRows = exceptions.data?.exceptions || [];
  const exceptionControls = useTableControls(exceptionRows);
  const paymentControls = useTableControls(payments.data);
  const [receipt, setReceipt] = useState(null);
  const [reconciling, setReconciling] = useState(null);
  const [transactionReference, setTransactionReference] = useState("");
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState("");

  async function openReceipt(paymentId) {
    try {
      const data = await api.get(`/fees/payments/${paymentId}/receipt/`);
      setReceipt(data);
    } catch (err) {
      push(err.message || "The receipt could not be loaded.", "error");
    }
  }

  async function saveReconciliation(event) {
    event.preventDefault();
    setBusy(true);
    setFormError("");
    try {
      await api.post(`/fees/payments/${reconciling.payment_id}/reconcile/`, {
        transaction_reference: transactionReference,
        notes,
      });
      push("Payment reconciled and receipt updated.", "success");
      setReconciling(null);
      setTransactionReference("");
      setNotes("");
      exceptions.reload();
      payments.reload();
    } catch (err) {
      setFormError(err.message || "The payment could not be reconciled.");
    } finally {
      setBusy(false);
    }
  }

  if (summary.loading || exceptions.loading || payments.loading) return <p className="muted" role="status">Loading fee ledger…</p>;
  const totals = summary.data || {};

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">School office</div>
          <h1>Fee ledger &amp; receipts</h1>
          <p className="muted">Locally recorded invoices and payments. No gateway credentials are stored.</p>
        </div>
        <div className="actions">
          <Link className="button-link secondary" to="/admin/fees/invoices"><RollingLabel>Invoices</RollingLabel></Link>
          <Link className="button-link ghost" to="/admin/fees/payments"><RollingLabel>Record payment</RollingLabel></Link>
        </div>
      </div>

      {(summary.error || exceptions.error || payments.error) && (
        <div className="notice error" role="alert">
          {summary.error || exceptions.error || payments.error}
        </div>
      )}

      <div className="stat-grid">
        <StatCard label="Invoices" value={totals.invoices ?? "—"} />
        <StatCard label="Billed" value={money(totals.amount_due)} />
        <StatCard label="Recorded" value={money(totals.amount_paid)} />
        <StatCard label="Outstanding" value={money(totals.balance)} />
      </div>

      <h2 style={{ marginTop: "1.5rem" }}>Reconciliation exceptions</h2>
      <div className="notice warn">
        Mobile-money payments are marked as needing review until the transaction message is checked.
        A transaction code can only be used once per school.
      </div>
      <TableToolbar
        title="exceptions"
        controls={exceptionControls}
        onRefresh={() => { exceptions.reload(); payments.reload(); }}
      />
      <DataTable
        columns={[
          { key: "reference", label: "Receipt" },
          { key: "learner_name", label: "Learner" },
          { key: "amount", label: "Amount", render: (row) => money(row.amount) },
          { key: "method", label: "Method" },
          { key: "transaction_reference", label: "Transaction code", render: (row) => row.transaction_reference || "—" },
          {
            key: "reason",
            label: "Reason",
            render: (row) => <span className="tag warn">{row.reason.replaceAll("_", " ").toLowerCase()}</span>,
          },
          {
            key: "actions",
            label: "Actions",
            render: (row) => (
              <button
                type="button"
                className="secondary small"
                aria-label={`Reconcile receipt ${row.reference}`}
                onClick={() => {
                  setReconciling(row);
                  setTransactionReference(row.transaction_reference || "");
                  setNotes("");
                }}
              >
                <RollingLabel>Reconcile</RollingLabel>
              </button>
            ),
          },
        ]}
        rows={exceptionControls.visibleRows}
        loading={false}
        error={null}
        emptyTitle="No exceptions"
        emptyHint="Every recorded payment has a transaction code or is not a mobile payment."
      />
      <TablePagination controls={exceptionControls} />

      <h2 style={{ marginTop: "1.5rem" }}>Receipts</h2>
      <DataTable
        columns={[
          { key: "reference", label: "Receipt" },
          { key: "invoice_reference", label: "Invoice" },
          { key: "amount", label: "Amount", render: (row) => money(row.amount) },
          { key: "method", label: "Method" },
          {
            key: "reconciliation_status",
            label: "Reconciliation",
            render: (row) => (
              <span className={`tag ${row.reconciliation_status === "RECONCILED" ? "good" : "warn"}`}>
                {row.reconciliation_status.replaceAll("_", " ").toLowerCase()}
              </span>
            ),
          },
          { key: "paid_at", label: "Recorded", render: (row) => formatDateTime(row.paid_at) },
          {
            key: "actions",
            label: "Actions",
            render: (row) => (
              <button
                type="button"
                className="ghost small"
                aria-label={`View receipt ${row.reference}`}
                onClick={() => openReceipt(row.id)}
              >
                <RollingLabel>View receipt</RollingLabel>
              </button>
            ),
          },
        ]}
        rows={paymentControls.visibleRows}
        loading={false}
        error={null}
        emptyTitle="No payments recorded"
        emptyHint="Record a payment against an invoice to issue a receipt."
      />
      <TablePagination controls={paymentControls} />

      {receipt && (
        <Modal title={`Receipt ${receipt.receipt_number}`} onClose={() => setReceipt(null)}>
          <div className="receipt-sheet">
            <h2>{receipt.school_name || "School"}</h2>
            {receipt.school_code && <p className="muted">{receipt.school_code}</p>}
            <dl className="detail-list">
              <div><dt>Receipt number</dt><dd className="mono">{receipt.receipt_number}</dd></div>
              <div><dt>Recorded</dt><dd>{formatDateTime(receipt.paid_at)}</dd></div>
              <div><dt>Learner</dt><dd>{receipt.learner_name} ({receipt.admission_number})</dd></div>
              <div><dt>Invoice</dt><dd className="mono">{receipt.invoice_reference}</dd></div>
              <div><dt>Fee</dt><dd>{receipt.fee_name || "—"}</dd></div>
              <div><dt>Amount</dt><dd><strong>{money(receipt.amount)}</strong></dd></div>
              <div><dt>Method</dt><dd>{receipt.method}</dd></div>
              <div><dt>Transaction code</dt><dd className="mono">{receipt.transaction_reference || "—"}</dd></div>
              <div><dt>Payer phone</dt><dd>{receipt.payer_phone || "—"}</dd></div>
              <div><dt>Recorded by</dt><dd>{receipt.recorded_by_name || "—"}</dd></div>
              <div><dt>Status</dt><dd>{receipt.reconciliation_status}</dd></div>
            </dl>
          </div>
          <div className="form-actions">
            <button type="button" className="ghost" onClick={() => setReceipt(null)}>
              <RollingLabel>Close</RollingLabel>
            </button>
            <button type="button" onClick={() => window.print()}>
              <RollingLabel>Print receipt</RollingLabel>
            </button>
          </div>
        </Modal>
      )}

      {reconciling && (
        <Modal title={`Reconcile ${reconciling.reference}`} onClose={() => setReconciling(null)}>
          <form onSubmit={saveReconciliation}>
            {formError && <div className="notice error" role="alert">{formError}</div>}
            <FormField label="Transaction code" hint="The code from the M-Pesa message, checked against the office record.">
              <input
                type="text"
                value={transactionReference}
                onChange={(event) => setTransactionReference(event.target.value)}
                required={reconciling.method === "MOBILE"}
              />
            </FormField>
            <FormField label="Notes (optional)">
              <textarea value={notes} onChange={(event) => setNotes(event.target.value)} rows={3} />
            </FormField>
            <div className="form-actions">
              <button type="button" className="ghost" onClick={() => setReconciling(null)}>
                <RollingLabel>Cancel</RollingLabel>
              </button>
              <button type="submit" disabled={busy} aria-busy={busy || undefined}>
                {busy ? "Saving…" : <RollingLabel>Confirm reconciliation</RollingLabel>}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </section>
  );
}
