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

export function MeetingDetails({ meeting, zone, setZone, backHref, onBack }: {
  meeting: Meeting; zone: string; setZone: (zone: string) => void; backHref: string; onBack: () => void;
}) {
  const zones = Intl.supportedValuesOf("timeZone");
  return <section className="meeting-details" aria-labelledby="detail-title">
    <a href={backHref} className="back-link" onClick={(event) => { if (!event.ctrlKey && !event.metaKey) { event.preventDefault(); onBack(); } }}>
      <ArrowLeft size={18} aria-hidden="true" /> Back to schedule
    </a>
    <div className="detail-heading">
      <div><p>{meeting.competition}{meeting.round ? ` / Round ${meeting.round}` : ""}</p><h2 id="detail-title">{meeting.name}</h2><p>{meeting.circuit}</p></div>
      <label>Display time zone<select aria-label="Display time zone" value={zone} onChange={(event) => setZone(event.target.value)}>
        <option value="browser">Browser local</option><option value="event">Event local</option><option value="UTC">UTC</option>
        {zones.map((name) => <option key={name} value={name}>{name.replaceAll("_", " ")}</option>)}
      </select></label>
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
    <div className="detail-provenance"><a href={meeting.sourceUrl} target="_blank" rel="noreferrer"><ExternalLink size={16} aria-hidden="true" /> Official source</a>
      <span>Retrieved {meeting.retrievedAt}</span><span className="publication-version">Publication {meeting.publicationVersion}</span></div>
  </section>;
}