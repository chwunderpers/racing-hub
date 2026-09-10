import { ArrowLeft, ExternalLink } from "lucide-react";
import type { components } from "./api/schema";

type Meeting = components["schemas"]["MeetingResponse"];
type Clock = components["schemas"]["TimeResponse"];

function SessionTime({ clock, zone, eventZone }: { clock: Clock; zone: string; eventZone?: string | null }) {
  if (!clock.instant) return <span>{clock.local} (unresolved)</span>;
  const selectedZone = zone === "browser" ? Intl.DateTimeFormat().resolvedOptions().timeZone : zone === "event" ? clock.zone || eventZone : zone;
  if (!selectedZone) return <span>{clock.local} (event zone unavailable)</span>;
  try {
    const label = new Intl.DateTimeFormat("en-GB", {
      timeZone: selectedZone, day: "numeric", month: "short", year: "numeric",
      hour: "2-digit", minute: "2-digit", second: clock.local.length > 16 ? "2-digit" : undefined,
      hourCycle: "h23", timeZoneName: "short",
    }).format(new Date(clock.instant));
    return <time dateTime={clock.instant}>{label}</time>;
  } catch {
    return <span>{clock.local} (display zone unavailable)</span>;
  }
}

export function MeetingDetails({ meeting, meetings, meetingHref, onMeeting, zone, setZone, backHref, onBack }: {
  meeting: Meeting; meetings: Meeting[]; meetingHref: (identity: string) => string; onMeeting: (identity: string) => void;
  zone: string; setZone: (zone: string) => void; backHref: string; onBack: () => void;
}) {
  const zones = Intl.supportedValuesOf("timeZone");
  const related = meeting.circuitId ? meetings.filter((entry) => entry.id !== meeting.id && entry.circuitId === meeting.circuitId) : [];
  const shared = related.some((entry) => entry.competitionId && entry.competitionId !== meeting.competitionId);
  return <section className="meeting-details" aria-labelledby="detail-title">
    <a href={backHref} className="back-link" onClick={(event) => { if (!event.ctrlKey && !event.metaKey) { event.preventDefault(); onBack(); } }}>
      <ArrowLeft size={18} aria-hidden="true" /> Back to schedule
    </a>
    <div className="detail-heading">
      <div><p>{meeting.competition}{meeting.round ? ` / Round ${meeting.round}` : meeting.kind === "prologue" ? " / Prologue" : meeting.kind === "test" ? " / Test" : ""}</p><h2 id="detail-title">{meeting.name}</h2><p>{meeting.circuit}</p><p><time dateTime={meeting.startDate}>{meeting.startDate}</time> - <time dateTime={meeting.endDate}>{meeting.endDate}</time></p></div>
      {Boolean(meeting.sessions?.length) && <label>Display time zone<select aria-label="Display time zone" value={zone} onChange={(event) => setZone(event.target.value)}>
        <option value="browser">Browser local</option><option value="event">Event local</option><option value="UTC">UTC</option>
        {zones.map((name) => <option key={name} value={name}>{name.replaceAll("_", " ")}</option>)}
      </select></label>}
    </div>
    {meeting.status === "cancelled" && <strong className="stale-notice">Meeting cancelled</strong>}
    <div className="session-list">
      {(meeting.sessions || []).map((session) => <article key={session.id} className="session-row">
        <div><h3>{session.name}</h3><span className="session-status">{session.status}</span></div>
        <div className="session-times"><SessionTime clock={session.start} zone={zone} eventZone={meeting.eventTimezone} />
          {session.end && <span>Scheduled end: <SessionTime clock={session.end} zone={zone} eventZone={meeting.eventTimezone} /></span>}
          <span className="source-clock">Published: {session.start.local}{session.start.offset ? ` ${session.start.offset}` : ""}{session.start.zone ? ` (${session.start.zone})` : ""}</span>
        </div>
      </article>)}
      {!(meeting.sessions || []).length && <p>Session times not published</p>}
    </div>
    {shared && <section className="shared-circuit" aria-labelledby="shared-circuit-title">
      <h3 id="shared-circuit-title">Shared circuit</h3>
      <ul>{related.map((entry) => <li key={entry.id}>
        <a href={meetingHref(entry.id)} onClick={(event) => { if (!event.ctrlKey && !event.metaKey) { event.preventDefault(); onMeeting(entry.id); } }}>{entry.name}</a>
        <span>{entry.competition} / {entry.startDate}</span>
      </li>)}</ul>
    </section>}
    {Boolean(meeting.fieldAssertions?.length) && <details className="field-provenance" key={meeting.id}>
      <summary>Source assertions ({meeting.fieldAssertions!.length})</summary>
      <dl>{meeting.fieldAssertions!.map((assertion, index) => <div key={index}>
        <dt>{assertion.field.replaceAll("_", " ")} <span>{assertion.preferred ? "Preferred" : "Retained alternative"}</span></dt>
        <dd><p className="assertion-value">{assertion.value || "(empty)"}</p><p>{assertion.rule}</p>
          <a href={assertion.source_url} target="_blank" rel="noreferrer">{assertion.locator}</a><span>Retrieved {assertion.retrieved_at}</span>
        </dd>
      </div>)}</dl>
    </details>}
    <div className="detail-provenance"><a href={meeting.sourceUrl} target="_blank" rel="noreferrer"><ExternalLink size={16} aria-hidden="true" /> Official source</a>
      <span>Retrieved {meeting.retrievedAt}</span><span className="publication-version">Publication {meeting.publicationVersion}</span></div>
  </section>;
}