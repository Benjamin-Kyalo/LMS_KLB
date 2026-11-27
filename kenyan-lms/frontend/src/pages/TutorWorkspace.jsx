import { useState } from "react";
import { useList, useResource } from "../hooks/useApi";
import { api } from "../services/api";
import { useToast } from "../context/ToastContext";
import Loading from "../components/Loading";
import FormField from "../components/FormField";
import RollingLabel from "../components/RollingLabel";
import { useSiteContent } from "../context/SiteContentContext";
import { useSectionStyle } from "../styles/sectionStyles";

function asText(value) {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "string") return value;
  if (Array.isArray(value)) return value.map(asText).join(", ");
  if (typeof value === "object") return value.label || value.code || value.name || JSON.stringify(value);
  return String(value);
}

// Curriculum-grounded assistant. Local and deterministic by default.
export default function TutorWorkspace({ portal = false }) {
  const { push } = useToast();
  const { content } = useSiteContent();
  const siteMessages = content.messages || {};
  const somethingWrong = siteMessages.errors?.somethingWrong
    || "We could not complete that action. Try again, or contact support if the problem continues. Include the reference number shown on this page.";
  const resourcesLoading = siteMessages.loading?.[2] || "Opening your learning resources...";
  const tutorNavLabel = (content.app?.portalNav || []).find((item) => item.key === "tutor")?.label || "Ask the tutor";
  const sectionStyle = useSectionStyle("tutor");
  const conversations = useList("/tutor/conversations/");
  const health = useResource("/tutor/conversations/health/");
  const policy = health.data?.policy;
  const [activeId, setActiveId] = useState(null);
  const [newTitle, setNewTitle] = useState("");
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [last, setLast] = useState(null);

  const active = activeId || conversations.data[0]?.id || null;
  const messages = useResource(active ? `/tutor/messages/?conversation=${active}` : null);

  async function ask(e) {
    e.preventDefault();
    if (!active || !question.trim()) return;
    setBusy(true);
    try {
      const answer = await api.post(`/tutor/conversations/${active}/ask/`, { question: question.trim() });
      setLast(answer);
      setQuestion("");
      messages.reload();
    } catch (err) {
      push(err.message || somethingWrong, "error");
    } finally {
      setBusy(false);
    }
  }

  if (conversations.loading) return <Loading label={resourcesLoading} />;

  const messageRows = Array.isArray(messages.data)
    ? messages.data
    : messages.data?.results || [];
  const shown = last && active === (last.conversation || active) ? [last] : messageRows;

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="overline">Learning support</div>
          <h1>{portal ? tutorNavLabel : "Curriculum tutor"}</h1>
        </div>
      </div>

      <div className="tutor-intro section-styled" style={sectionStyle}>
        <img
          src={content.portal?.tutorImageSrc || "/images/tutor-brain.jpg"}
          alt={content.portal?.tutorImageAlt || ""}
          className="tutor-intro-photo"
        />
        <div>
          <h2>Learn with a clear next step</h2>
          <p className="muted">
            Ask about a topic, outcome or textbook. Answers come from the records your school holds.
          </p>
        </div>
      </div>

      <div className="notice" style={{ marginBottom: "1rem" }}>
        This assistant answers only from curriculum and resource records held by your school.
        By default it runs locally and makes no external calls. If it cannot find a record, it
        says so instead of guessing.
        {health.data?.provider && <> Active provider: <strong>{asText(health.data.provider)}</strong>.</>}
        {policy && (
          <div className="muted" style={{ marginTop: "0.5rem" }}>
            Policy v{asText(policy.policy_version)}: sources are limited to stored curriculum
            and resource records. Learner, assessment, fee and message records are never sent.
            {policy.external_provider_configured
              ? " Remote answers are accepted only when they are verbatim excerpts of the local answer."
              : " No external AI provider is configured."}
          </div>
        )}
      </div>

      <div className="two-column">
        <div className="panel panel-pad">
          <h2 style={{ marginTop: 0 }}>Conversations</h2>
          {!conversations.data.length && <p className="muted">No conversations yet. Start one below.</p>}
          <div className="stack">
            {conversations.data.map((row) => (
              <button
                key={row.id}
                className={row.id === active ? "button" : "button secondary"}
                aria-pressed={row.id === active}
                onClick={() => { setActiveId(row.id); setLast(null); }}
              >
                {row.title || (row.reference ? `Conversation ${row.reference}` : `Conversation ${row.id}`)}
              </button>
            ))}
          </div>
          <form
            style={{ marginTop: "1rem" }}
            onSubmit={async (e) => {
              e.preventDefault();
              const title = newTitle.trim();
              if (!title) return;
              try {
                const created = await api.post("/tutor/conversations/", { title });
                conversations.reload();
                setActiveId(created.id);
                setNewTitle("");
              } catch (err) { push(err.message || somethingWrong, "error"); }
            }}
          >
            <FormField label="New conversation" full>
              <input
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder={portal ? "e.g. Fractions practice" : "e.g. Grade 6 revision"}
              />
            </FormField>
            <div className="form-actions">
              <button type="submit" className="ghost" disabled={!newTitle.trim()}><RollingLabel>Start conversation</RollingLabel></button>
            </div>
          </form>
        </div>

        <div className="panel panel-pad">
          <h2 style={{ marginTop: 0 }}>Conversation</h2>
          {!active && <p className="muted">Select a conversation, or create one, to begin.</p>}
          {active && (
            <>
              <div className="stack" style={{ marginBottom: "1rem" }}>
                {!shown.length && <p className="muted">Ask a question about a topic, outcome or textbook.</p>}
                {shown.map((message, index) => (
                  <div key={message.id || index} className={`notice ${message.role === "TUTOR" ? "success" : ""}`}>
                    <div className="overline">{message.role === "TUTOR" ? "Tutor" : "You"}</div>
                    <div>{message.body || message.answer || asText(message)}</div>
                    {Array.isArray(message.sources) && message.sources.length > 0 && (
                      <div className="muted" style={{ marginTop: "0.5rem" }}>
                        Sources: {message.sources.map(asText).join(" · ")}
                      </div>
                    )}
                    {Array.isArray(message.suggestions) && message.suggestions.length > 0 && (
                      <div className="muted" style={{ marginTop: "0.25rem" }}>
                        Next: {message.suggestions.map(asText).join(" · ")}
                      </div>
                    )}
                    {message.policy?.policy_version && (
                      <div className="muted" style={{ marginTop: "0.25rem" }}>
                        Answer policy v{asText(message.policy.policy_version)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
              <form onSubmit={ask}>
                <FormField label="Your question" full>
                  <textarea rows={3} value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="e.g. What outcomes cover fractions in Grade 6?" />
                </FormField>
                <div className="form-actions">
                  <button type="submit" disabled={busy || !question.trim()}>{busy ? "Thinking…" : <RollingLabel>Ask</RollingLabel>}</button>
                </div>
              </form>
            </>
          )}
        </div>
      </div>
    </section>
  );
}
