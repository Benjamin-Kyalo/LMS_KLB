import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="panel panel-pad" style={{ margin: "3rem auto", maxWidth: 420, textAlign: "center" }}>
      <div className="overline">404</div>
      <h1>Page not found</h1>
      <p className="muted">The page you asked for does not exist.</p>
      <Link to="/">Back to dashboard</Link>
    </div>
  );
}
