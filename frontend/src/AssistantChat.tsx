import { useEffect, useRef, useState } from "react";
import { ExternalLink, RotateCcw, Send, Square } from "lucide-react";
import type { components } from "./api/schema";
import "./AssistantChat.css";

type Answer = components["schemas"]["AssistantAnswer"];
type Turn = { question: string; answer?: Answer };
const base = import.meta.env.VITE_API_BASE_URL ?? "";

export function AssistantChat({ zone, setZone }: { zone: string; setZone: (zone: string) => void }) {
  const [token, setToken] = useState("");
  const [available, setAvailable] = useState(false);
  const [message, setMessage] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [generation, setGeneration] = useState(0);
  const activeRequest = useRef<AbortController | null>(null);
  const transcript = useRef<HTMLDivElement>(null);
  const activeToken = useRef("");

  useEffect(() => {
    let active = true;
    setToken("");
    setAvailable(false);
    fetch(`${base}/api/assistant/sessions`, { method: "POST" })
      .then(async response => {
        if (!response.ok) throw new Error();
        return await response.json() as components["schemas"]["AssistantSessionResponse"];
      })
      .then(session => {
        if (!active) {
          void fetch(`${base}/api/assistant/session`, { method: "DELETE", headers: { "X-Assistant-Session": session.sessionToken } }).catch(() => {});
          return;
        }
        activeToken.current = session.sessionToken;
        setToken(session.sessionToken);
        setAvailable(session.available);
        if (!session.available) setError("Assistant is not configured.");
      }).catch(() => { if (active) setError("Assistant unavailable. Start a new conversation to retry."); });
    return () => {
      active = false;
      activeRequest.current?.abort();
      if (activeToken.current) void fetch(`${base}/api/assistant/session`, { method: "DELETE", headers: { "X-Assistant-Session": activeToken.current }, keepalive: true }).catch(() => {});
      activeToken.current = "";
    };
  }, [generation]);

  useEffect(() => {
    transcript.current?.scrollTo?.({ top: transcript.current.scrollHeight });
  }, [turns, busy]);

  function reset() {
    activeRequest.current?.abort();
    setTurns([]);
    setMessage("");
    setError("");
    setBusy(false);
    setGeneration(value => value + 1);
  }

  async function send() {
    if (!message.trim() || !token || busy) return;
    const question = message.trim();
    const controller = new AbortController();
    activeRequest.current = controller;
    setTurns(previous => [...previous, { question }]);
    setMessage("");
    setError("");
    setBusy(true);
    try {
      const response = await fetch(`${base}/api/assistant/messages`, {
        method: "POST", signal: controller.signal,
        headers: { "Content-Type": "application/json", "X-Assistant-Session": token },
        body: JSON.stringify({ message: question, displayTimeZone: zone }),
      });
      if (!response.ok) throw new Error(response.status === 410 ? "Conversation expired. Start a new conversation." : response.status === 400 ? "Request or conversation limit reached. Start a new conversation." : "Assistant temporarily unavailable. Try again.");
      const answer = await response.json() as Answer;
      if (!controller.signal.aborted) setTurns(previous => previous.map((turn, index) => index === previous.length - 1 ? { ...turn, answer } : turn));
    } catch (failure) {
      if (!controller.signal.aborted) setError(failure instanceof Error ? failure.message : "Assistant unavailable.");
    } finally {
      if (activeRequest.current === controller) setBusy(false);
    }
  }

  return <section className="assistant-section" aria-labelledby="assistant-title">
    <div className="assistant-heading"><h2 id="assistant-title">Ask Racing Hub</h2>
      <div className="assistant-controls"><label>Answer time zone<select aria-label="Answer time zone" value={zone} onChange={event => setZone(event.target.value)}>
        <option value="UTC">UTC</option>{Intl.supportedValuesOf("timeZone").map(name => <option key={name} value={name}>{name.replaceAll("_", " ")}</option>)}
      </select></label><button type="button" className="assistant-icon" aria-label="New conversation" title="New conversation" onClick={reset}><RotateCcw size={20} /></button></div>
    </div>
    <div className="assistant-transcript" role="log" aria-label="Conversation" ref={transcript}>
      {turns.map((turn, index) => <article className="assistant-turn" key={index}><h3>{turn.question}</h3>
        {turn.answer && <><p className="assistant-answer">{turn.answer.text}</p>
          <p className="assistant-answer-meta">Display time zone: {turn.answer.displayTimeZone}</p>
          <p className="assistant-answer-meta">{turn.answer.classification === "derived" ? "Derived answer" : turn.answer.classification === "unsupported" ? "Evidence unavailable" : "Sourced answer"}{turn.answer.freshness.stale ? " / Sources may be outdated" : " / Source checks current"}</p>
          <ul className="assistant-citations">{turn.answer.citations.map(citation => <li key={citation.id}>
            <a href={citation.sourceUrl} target="_blank" rel="noreferrer"><ExternalLink size={14} aria-hidden="true" />{citation.title}</a>
            {citation.retrievedAt && <span>Retrieved {citation.retrievedAt}</span>}
          </li>)}</ul></>}
      </article>)}
      {busy && <p role="status">Checking published sources...</p>}
    </div>
    {error && <p className="assistant-error" role="alert">{error}</p>}
    <form className="assistant-composer" onSubmit={event => { event.preventDefault(); void send(); }}>
      <label className="assistant-question">Question<textarea aria-label="Question" value={message} onChange={event => setMessage(event.target.value)} maxLength={2000} rows={2} disabled={!available} /></label>
      {busy ? <button type="button" className="assistant-icon" aria-label="Cancel reply" title="Cancel reply" onClick={reset}><Square size={20} /></button> : <button type="submit" className="assistant-icon" aria-label="Send question" title="Send question" disabled={!available || !token || !message.trim()}><Send size={20} /></button>}
    </form>
  </section>;
}