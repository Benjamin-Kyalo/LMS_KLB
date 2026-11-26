import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useList, useResource } from "../hooks/useApi";
import { api } from "../services/api";
import Loading from "../components/Loading";
import RollingLabel from "../components/RollingLabel";
import { homeFor, isGuardian, isTeacher, roleLabel } from "../utilities/roles";

const STEP_HELP = {
  profile_complete: "Check your name, email and phone number, then confirm they are correct.",
  teacher_approved: "A school administrator reviews teacher accounts before they can sign in.",
  classes_assigned: "Your administrator assigns at least one class and subject to your account.",
  guardian_link_verified: "Enter your learner's admission number; the school verifies the link before reports open.",
};

export default function Onboarding() {
  const { user, setUser } = useAuth();
  const checklist = useResource("/auth/onboarding/me/");
  const links = useList("/learners/link-requests/");
  const [pendingAction, setPendingAction] = useState("");
  const [identifier, setIdentifier] = useState("");
  const [error, setError] = useState(null);

  async function confirmProfile() {
    setPendingAction("profile");
    setError(null);
    try {
      await api.patch("/auth/onboarding/me/", { profile_complete: true });
      checklist.reload();
      setUser(await api.get("/auth/me/"));
    } catch (err) {
      setError(err.message);
    } finally {
      setPendingAction("");
    }
  }

  async function submitLink(event) {
    event.preventDefault();
    setPendingAction("link");
    setError(null);
    try {
      await api.post("/learners/link-requests/", {
        learner_identifier: identifier.trim(),
        relationship: user?.relationship_to_learner || "",
      });
      setIdentifier("");
      links.reload();
    } catch (err) {
      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      setPendingAction("");
    }
  }

  if (!user) return <Loading />;
  if (checklist.loading) return <Loading />;

  const steps = checklist.data?.steps || [];
  const complete = Boolean(checklist.data?.is_complete);
  const guardian = isGuardian(user);
  const teacher = isTeacher(user);

  return (
    <section className="onboarding-page">
      <div className="page-head">
        <div>
          <div className="overline">First-time setup</div>
          <h1>Welcome, {user.first_name || user.username}</h1>
          <p className="muted" style={{ marginTop: "0.2rem" }}>
            You are signed in as {roleLabel(user)}. Complete these steps to unlock your workspace.
          </p>
        </div>
      </div>

      {checklist.error && <div className="notice error" role="alert">{checklist.error}</div>}
      {error && <div className="notice error" role="alert">{error}</div>}

      <div className="onboarding-grid">
        <div className="panel panel-pad">
          <h2>Your setup checklist</h2>
          <p className="muted">Steps checked by the school are updated automatically.</p>
          <ol className="onboarding-steps">
            {steps.map((step) => (
              <li key={step.key} className={step.done ? "done" : ""}>
                <span className="step-mark" aria-hidden="true">{step.done ? "✓" : "•"}</span>
                <div>
                  <strong>{step.label}</strong>
                  <p className="muted">{STEP_HELP[step.key]}</p>
                </div>
                <span className={`tag ${step.done ? "good" : ""}`}>{step.done ? "Done" : "Pending"}</span>
              </li>
            ))}
          </ol>
          {!checklist.data?.profile_complete ? (
            <button
              onClick={confirmProfile}
              disabled={Boolean(pendingAction)}
              aria-busy={pendingAction === "profile" || undefined}
            >
              {pendingAction === "profile" ? "Confirming…" : <RollingLabel>Confirm my details</RollingLabel>}
            </button>
          ) : (
            <p className="notice success" role="status">Your profile details are confirmed.</p>
          )}
        </div>

        <div className="panel panel-pad">
          <h2>What happens next</h2>
          {teacher && (
            <p>
              Your account stays inactive until a school administrator approves it. Once approved,
              you can sign in and work on your assigned classes.
            </p>
          )}
          {guardian && (
            <>
              <p>
                Link a learner using the admission or assessment number issued by the school.
                Nothing from the learner record is visible until the school verifies the link.
              </p>
              <form onSubmit={submitLink} className="onboarding-link-form">
                <label>
                  Learner admission or assessment number
                  <input value={identifier} onChange={(event) => setIdentifier(event.target.value)} required />
                </label>
                <button
                  type="submit"
                  className="secondary"
                  disabled={Boolean(pendingAction) || !identifier.trim()}
                  aria-busy={pendingAction === "link" || undefined}
                >
                  {pendingAction === "link" ? "Submitting link…" : <RollingLabel>Submit learner link</RollingLabel>}
                </button>
              </form>
              <h3 style={{ marginTop: "1rem" }}>Your link requests</h3>
              {links.loading ? <Loading /> : links.error ? (
                <div className="notice error" role="alert">{links.error}</div>
              ) : links.data.length ? (
                <ul className="compact-list">
                  {links.data.map((row) => (
                    <li key={row.id}>
                      <strong>{row.admission_number || row.learner_identifier}</strong>{" "}
                      <span className={`tag ${row.status === "VERIFIED" ? "good" : row.status === "REJECTED" ? "bad" : ""}`}>
                        {row.status}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="muted">No learner link submitted yet.</p>
              )}
            </>
          )}
          {!teacher && !guardian && (
            <p>Your workspace is ready once you confirm your profile details.</p>
          )}
          {complete ? (
            <p className="notice success" role="status" style={{ marginTop: "1rem" }}>
              Setup complete. <Link to={homeFor(user)}>Open your workspace →</Link>
            </p>
          ) : (
            <p className="muted" style={{ marginTop: "1rem" }}>
              Your workspace link becomes available when every step above is done.
            </p>
          )}
        </div>
      </div>
    </section>
  );
}
