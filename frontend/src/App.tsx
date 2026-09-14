import { useEffect, useState } from "react";
import {
  Activity,
  CalendarDays,
  ExternalLink,
  Flag,
  FlaskConical,
  Gauge,
  MapPin,
  MessageCircle,
  Trophy,
} from "lucide-react";

import { getHealth, getSchedule } from "./api/client";
import type { components } from "./api/schema";
import { MeetingDetails } from "./MeetingDetails";
import { MeetingCapabilities } from "./MeetingCapabilities";
import { AssistantChat } from "./AssistantChat";
import { Vehicles } from "./Vehicles";
import { Exports } from "./Exports";
import "./styles.css";

type Meeting = components["schemas"]["MeetingResponse"];
type ViewState =
  | "loading"
  | "ready"
  | "database-unavailable"
  | "unavailable";

const dateFormatter = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "long",
  timeZone: "UTC",
  year: "numeric",
});

const retrievalFormatter = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "long",
  timeZone: "UTC",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});

function formatDateRange(startDate: string, endDate: string): string {
  const start = new Date(`${startDate}T00:00:00Z`);
  const end = new Date(`${endDate}T00:00:00Z`);
  if (
    start.getUTCMonth() === end.getUTCMonth() &&
    start.getUTCFullYear() === end.getUTCFullYear()
  ) {
    return `${start.getUTCDate()}-${dateFormatter.format(end)}`;
  }
  return `${dateFormatter.format(start)} - ${dateFormatter.format(end)}`;
}

function formatRetrieved(retrievedAt: string): string {
  return `${retrievalFormatter.format(new Date(retrievedAt)).replace(" at ", ", ")} UTC`;
}

function validFilterDate(value: string): boolean {
  if (!value) return true;
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const parsed = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value;
}

function App() {
  const [chatOpen, setChatOpen] = useState(false);
  const [viewState, setViewState] = useState<ViewState>("loading");
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [coverage, setCoverage] = useState<components["schemas"]["SeasonCoverageResponse"][]>([]);
  const [freshness, setFreshness] = useState<components["schemas"]["FreshnessResponse"] | null>(null);
  const [query, setQuery] = useState(() => new URLSearchParams(window.location.search));
  const queryFor = (key: string, value: string) => {
    const next = new URLSearchParams(query);
    if (value) next.set(key, value); else next.delete(key);
    return `?${next.toString()}`;
  };
  const changeQuery = (key: string, value: string) => {
    const url = queryFor(key, value);
    window.history.pushState({}, "", url);
    setQuery(new URLSearchParams(window.location.search));
  };
  useEffect(() => {
    const restore = () => setQuery(new URLSearchParams(window.location.search));
    window.addEventListener("popstate", restore);
    return () => window.removeEventListener("popstate", restore);
  }, []);
  const competition = query.get("competition") || "";
  const circuit = query.get("circuit") || "";
  const rawFrom = query.get("from") || "";
  const rawThrough = query.get("through") || "";
  const malformedDates = !validFilterDate(rawFrom) || !validFilterDate(rawThrough);
  const from = validFilterDate(rawFrom) ? rawFrom : "";
  const through = validFilterDate(rawThrough) ? rawThrough : "";
  const invalidDates = Boolean(from && through && from > through);
  const competitionOptions = new Map(meetings.map((meeting) => [meeting.competitionId || meeting.competition, meeting.competition]));
  for (const assessment of coverage) {
    if (!competitionOptions.has(assessment.competitionId)) competitionOptions.set(assessment.competitionId, assessment.competitionId.replace("competition:", ""));
  }
  const circuitOptions = new Map<string, string>();
  for (const meeting of meetings) {
    const identity = meeting.circuitId || meeting.circuit;
    if (!circuitOptions.has(identity)) circuitOptions.set(identity, meeting.circuit);
  }
  const filtered = meetings.filter((meeting) => !invalidDates && (!competition || (meeting.competitionId || meeting.competition) === competition)
    && (!circuit || (meeting.circuitId || meeting.circuit) === circuit) && (!from || meeting.endDate >= from) && (!through || meeting.startDate <= through));
  const selectedId = query.get("meeting");
  const selected = meetings.find((meeting) => meeting.id === selectedId);

  useEffect(() => {
    let active = true;

    Promise.all([getHealth(), getSchedule()])
      .then(([health, schedule]) => {
        if (active) {
          setMeetings(schedule.meetings);
          setCoverage(schedule.coverage || []);
          setFreshness(schedule.freshness || null);
          setViewState(health.status !== "ok" ? "database-unavailable" : "ready");
        }
      })
      .catch(() => {
        if (active) {
          setViewState("unavailable");
        }
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="app-shell">
      <header className="masthead">
        <a className="brand" href="/" aria-label="Racing Hub home">
          <span className="brand-mark" aria-hidden="true">
            <span />
            <span />
            <span />
          </span>
          <span>Racing Hub</span>
        </a>

        <button className="assistant-toggle" type="button" aria-expanded={chatOpen} onClick={() => setChatOpen(value => !value)}><MessageCircle size={20} aria-hidden="true" />Ask</button>
        <div className={`system-status system-status--${viewState}`} role="status">
          <Activity size={16} aria-hidden="true" />
          <span>
            {viewState === "loading" && "Connecting"}
            {viewState === "ready" && "System ready"}
            {viewState === "database-unavailable" && "Database unavailable"}
            {viewState === "unavailable" && "Backend unavailable"}
          </span>
        </div>
      </header>

      <main>
        {chatOpen && <AssistantChat zone={query.get("zone") === "event" ? selected?.eventTimezone || "UTC" : query.get("zone") && query.get("zone") !== "browser" ? query.get("zone")! : Intl.DateTimeFormat().resolvedOptions().timeZone} setZone={zone => changeQuery("zone", zone)} />}
        <nav className="section-nav" aria-label="Main views">
          <a href={queryFor("view", "")} aria-current={!["vehicles", "exports"].includes(query.get("view") || "") ? "page" : undefined} onClick={event => { event.preventDefault(); changeQuery("view", ""); }}>Schedule</a>
          <a href={queryFor("view", "vehicles")} aria-current={query.get("view") === "vehicles" ? "page" : undefined} onClick={event => { event.preventDefault(); changeQuery("view", "vehicles"); }}>Vehicles</a>
          <a href={queryFor("view", "exports")} aria-current={query.get("view") === "exports" ? "page" : undefined} onClick={event => { event.preventDefault(); changeQuery("view", "exports"); }}>Exports</a>
        </nav>
        {query.get("view") === "exports" ? <Exports /> : query.get("view") === "vehicles" ? <Vehicles identity={query.get("vehicle") || ""} href={identity => queryFor("vehicle", identity)} navigate={identity => changeQuery("vehicle", identity)} /> : <>
        <section className="schedule-heading" aria-labelledby="schedule-title">
          <div>
            <p className="date-line">2026 season</p>
            <h1 id="schedule-title">Race schedule</h1>
          </div>
          <div className="season-stamp" aria-label="Current season">
            <Gauge size={18} aria-hidden="true" />
            <span>2026</span>
          </div>
        </section>

        <section className="filter-strip" aria-label="Schedule filters">
          <label className="filter-field">
            <Trophy size={17} aria-hidden="true" />
            <select aria-label="Competition" value={competition} onChange={(event) => changeQuery("competition", event.target.value)}>
              <option value="">All competitions</option>
              {[...competitionOptions].sort((first, second) => first[1].localeCompare(second[1])).map(([identity, name]) => <option key={identity} value={identity}>{name}</option>)}
            </select>
          </label>
          <label className="filter-field">
            <MapPin size={17} aria-hidden="true" />
            <select aria-label="Circuit" value={circuit} onChange={(event) => changeQuery("circuit", event.target.value)}>
              <option value="">All circuits</option>
              {[...circuitOptions].sort((first, second) => first[1].localeCompare(second[1])).map(([identity, name]) => <option key={identity} value={identity}>{name}</option>)}
            </select>
          </label>
          <div className="filter-field date-filter">
            <CalendarDays size={17} aria-hidden="true" />
            <div><label>From<input aria-label="From date" type="date" value={from} onChange={(event) => changeQuery("from", event.target.value)} /></label>
              <label>Through<input aria-label="Through date" type="date" value={through} onChange={(event) => changeQuery("through", event.target.value)} /></label></div>
          </div>
        </section>

        {viewState === "ready" && freshness?.stale && <p className="stale-notice" role="status">Schedule may be outdated. {freshness.reason}{freshness.lastSuccessAt ? ` Last verified ${formatRetrieved(freshness.lastSuccessAt)}.` : ""}</p>}
        {invalidDates && <p className="stale-notice" role="alert">From date must not follow through date.</p>}
        {malformedDates && <p className="stale-notice" role="alert">Date filters must use valid YYYY-MM-DD dates.</p>}
        {viewState === "ready" && !selectedId && coverage.filter((assessment) => !competition || assessment.competitionId === competition).map((assessment) => <div className="coverage-notice" key={`${assessment.competitionId}:${assessment.season}`}>
          <span>{competitionOptions.get(assessment.competitionId)} / {assessment.season}</span>
          <strong>{assessment.activity === "empty" ? "Officially empty schedule" : assessment.state === "complete" ? "Coverage complete" : assessment.state === "incomplete" ? "Coverage incomplete" : "Coverage unassessed"}</strong>
          <span>{assessment.reason}</span><a href={assessment.source_url} target="_blank" rel="noreferrer">Source</a>
        </div>)}
        {viewState === "ready" && selected && <MeetingDetails meeting={selected} meetings={meetings} meetingHref={(identity) => queryFor("meeting", identity)} onMeeting={(identity) => changeQuery("meeting", identity)} zone={query.get("zone") || "browser"} setZone={(zone) => changeQuery("zone", zone)} backHref={queryFor("meeting", "")} onBack={() => changeQuery("meeting", "")} />}
        {viewState === "ready" && selected && <MeetingCapabilities key={`${selected.id}:${selected.publicationVersion}`} identity={selected.id} publicationVersion={selected.publicationVersion} />}
        {viewState === "ready" && selectedId && !selected && <div className="empty-state"><h2>Meeting not found</h2><a href={queryFor("meeting", "")} onClick={(event) => { event.preventDefault(); changeQuery("meeting", ""); }}>Back to schedule</a></div>}

        <section className="schedule-lane" aria-live="polite" hidden={viewState === "ready" && Boolean(selectedId)}>
          {viewState === "loading" && (
            <div className="loading-state">
              <span className="loading-line" />
              <span>Loading schedule</span>
            </div>
          )}

          {viewState === "ready" && meetings.length === 0 && (
            <div className="empty-state">
              <div className="flag-box" aria-hidden="true">
                <Flag size={30} strokeWidth={1.5} />
              </div>
              <div>
                <h2>{coverage.length ? "No Meeting records in this publication" : "No meetings published yet"}</h2>
                {!coverage.length && <p>Coverage unassessed</p>}
              </div>
              <span className="empty-code">00</span>
            </div>
          )}

          {viewState === "ready" && meetings.length > 0 && (
            <div className="meeting-list">
              {filtered.map((meeting) => (
                <article className="meeting-row" key={meeting.id}>
                  <div className="meeting-round" aria-label={meeting.round ? `Round ${meeting.round}` : meeting.rounds?.length ? `Rounds ${meeting.rounds.map((round) => round.number).join(", ")}` : meeting.kind === "prologue" ? "Prologue" : meeting.kind === "test" ? "Test" : "Meeting"}>
                    {meeting.round ? String(meeting.round).padStart(2, "0") : meeting.rounds?.length === 1 ? String(meeting.rounds[0].number).padStart(2, "0") : meeting.rounds?.length ? <Flag size={24} aria-hidden="true" /> : <FlaskConical size={24} aria-hidden="true" />}
                  </div>
                  <div className="meeting-primary">
                    <p>{meeting.competition}</p>
                    <h2><a href={queryFor("meeting", meeting.id)} onClick={(event) => { if (!event.ctrlKey && !event.metaKey) { event.preventDefault(); changeQuery("meeting", meeting.id); } }}>{meeting.name}</a></h2>
                    {Boolean(meeting.rounds?.length) && <span className="meeting-kind">{meeting.rounds!.map((round) => `Round ${round.number}${round.status === "abandoned" ? " (abandoned)" : ""}`).join(" / ")}</span>}
                    {meeting.kind && meeting.kind !== "championship" && <span className="meeting-kind">{meeting.kind === "prologue" ? "Prologue" : "Test"}</span>}
                    {meeting.status === "cancelled" && <strong>Cancelled</strong>}
                    <span className="meeting-circuit">
                      <MapPin size={16} aria-hidden="true" />
                      {meeting.circuit}
                    </span>
                  </div>
                  <div className="meeting-timing">
                    <span className="meeting-dates">
                      {formatDateRange(meeting.startDate, meeting.endDate)}
                    </span>
                    <a href={meeting.sourceUrl} target="_blank" rel="noreferrer">
                      <ExternalLink size={15} aria-hidden="true" />
                      <span>{meeting.competition} source</span>
                    </a>
                    <span className="retrieved-at">
                      Retrieved {formatRetrieved(meeting.retrievedAt)}
                    </span>
                  </div>
                </article>
              ))}
            </div>
          )}
          {viewState === "ready" && meetings.length > 0 && filtered.length === 0 && <div className="empty-state"><h2>No meetings match these filters</h2></div>}

          {(viewState === "database-unavailable" || viewState === "unavailable") && (
            <div className="failure-state">
              <div className="failure-light" aria-hidden="true" />
              <div>
                <h2>Schedule service unavailable</h2>
                <p>
                  {viewState === "database-unavailable"
                    ? "The operational database is not ready. Try again shortly."
                    : "Check the backend connection, then reload this page."}
                </p>
              </div>
            </div>
          )}
        </section>
        </>}
      </main>

      <footer>
        <span>Local proof of concept</span>
        <span className="footer-rule" />
        <span>
          {viewState === "ready"
            ? meetings.length === 0
              ? coverage.length ? "Coverage assessment published" : "Awaiting first publication"
              : `${filtered.length} of ${meetings.length} meetings published`
            : "Service status"}
        </span>
      </footer>
    </div>
  );
}

export default App;