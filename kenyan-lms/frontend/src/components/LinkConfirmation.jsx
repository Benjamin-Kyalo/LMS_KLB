import PendingRequestActions from "./PendingRequestActions";

/**
 * Warnings and explicit consent shown before a guardian/learner link is saved.
 * Existing links are never hidden: the admin sees who is already connected and
 * must actively confirm before adding another link or proceeding with a
 * pending request.
 */
export default function LinkConfirmation({
  personLabel,
  existingLabel,
  existingNames = [],
  otherNames = [],
  pendingRequest,
  requestDetails,
  onRequestDecided,
  duplicate,
  confirmed,
  onConfirmedChange,
}) {
  const needsConfirmation = !duplicate && Boolean(
    existingNames.length || otherNames.length || pendingRequest
  );
  if (duplicate) {
    return (
      <div className="notice error" role="alert">
        This {personLabel} is already linked to that {existingLabel}. No new link is needed.
      </div>
    );
  }
  if (!needsConfirmation) return null;

  return (
    <div className="link-confirmation">
      {existingNames.length > 0 && (
        <div className="notice warn" role="status">
          This {existingLabel} is already linked to <strong>{existingNames.join(", ")}</strong>.
          Adding another {personLabel} also gives that account access.
        </div>
      )}
      {otherNames.length > 0 && (
        <div className="notice info" role="status">
          This {personLabel} is already linked to <strong>{otherNames.join(", ")}</strong>.
        </div>
      )}
      {pendingRequest && (
        <div className="notice warn" role="status">
          A link request (<strong>{pendingRequest.reference || pendingRequest.id}</strong>) is
          waiting for verification. Review it below, or reject it with a clear reason.
        </div>
      )}
      {pendingRequest && (
        <PendingRequestActions
          request={pendingRequest}
          details={requestDetails}
          onDecided={onRequestDecided}
        />
      )}
      <fieldset className="form-section">
        <legend>Confirm this link</legend>
        <label className="checkline">
          <input
            type="checkbox"
            checked={confirmed}
            onChange={(event) => onConfirmedChange(event.target.checked)}
            required
          />
          <span>I have reviewed the existing links above and want to continue.</span>
        </label>
      </fieldset>
    </div>
  );
}
