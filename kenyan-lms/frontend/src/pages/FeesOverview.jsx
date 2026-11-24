import { Link } from "react-router-dom";
import { useResource } from "../hooks/useApi";
import StatCard from "../components/StatCard";
import Loading from "../components/Loading";

const money = (value) => (value === null || value === undefined
  ? "—"
  : new Intl.NumberFormat("en-KE", { style: "currency", currency: "KES", maximumFractionDigits: 0 }).format(Number(value)));

// A school-office ledger summary. There is no gateway connection here.
export default function FeesOverview() {
  const summary = useResource("/fees/invoices/summary/");
  if (summary.loading) return <Loading />;

  const data = summary.data || {};
  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">School office</div>
          <h1>Fees</h1>
        </div>
        <div className="actions"><button className="secondary" onClick={summary.reload}>Refresh</button></div>
      </div>

      {summary.error && <div className="notice error" style={{ marginBottom: "1rem" }}>{summary.error}</div>}

      <div className="stat-grid">
        <StatCard label="Invoices" value={data.invoices ?? "—"} to="/admin/fees/invoices" />
        <StatCard label="Total billed" value={money(data.amount_due)} hint="Across the records you can see" />
        <StatCard label="Recorded payments" value={money(data.amount_paid)} to="/admin/fees/payments" />
        <StatCard label="Outstanding" value={money(data.balance)} to="/admin/fees/invoices" />
      </div>

      <div className="panel panel-pad" style={{ marginTop: "1.2rem" }}>
        <h2 style={{ marginTop: 0 }}>Manage the ledger</h2>
        <div className="row-actions">
          <Link className="button" to="/admin/fees/structures">Fee structures</Link>
          <Link className="button secondary" to="/admin/fees/invoices">Invoices</Link>
          <Link className="button secondary" to="/admin/fees/payments">Payments</Link>
        </div>
        <p className="muted" style={{ marginBottom: 0 }}>
          This is a local record of what the school has billed and received. No card details,
          mobile-money credentials or gateway tokens are stored, and no payment is taken here.
        </p>
      </div>
    </section>
  );
}
