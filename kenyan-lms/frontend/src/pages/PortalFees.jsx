import PortalList from "../components/PortalList";
import { statusTag } from "../utilities/format";

const money = (value) => (value === null || value === undefined
  ? "—"
  : new Intl.NumberFormat("en-KE", { style: "currency", currency: "KES", maximumFractionDigits: 0 }).format(Number(value)));

export default function PortalFees() {
  return (
    <section>
      <div className="notice" style={{ marginBottom: "1rem" }}>
        Fee visibility is controlled by your school. A parent or guardian sees invoices only for
        learners whose link explicitly allows fee access. No payment is taken in the portal.
      </div>
      <PortalList
        title="Fee invoices"
        overline="School office"
        endpoint="/fees/my-invoices/"
        columns={[
          { key: "reference", label: "Invoice", render: (r) => <span className="mono">{r.reference}</span> },
          { key: "learner_name", label: "Learner" },
          { key: "amount_due", label: "Billed", render: (r) => money(r.amount_due) },
          { key: "amount_paid", label: "Paid", render: (r) => money(r.amount_paid) },
          { key: "balance", label: "Balance", render: (r) => money(r.balance) },
          { key: "due_date", label: "Due" },
          { key: "status", label: "Status", render: (r) => statusTag(r.status) },
        ]}
        emptyHint="No fee invoices are visible for your account yet."
      />
    </section>
  );
}
