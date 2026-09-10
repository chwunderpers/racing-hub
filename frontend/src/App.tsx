import { useEffect, useState } from "react";
import {
  Activity,
  CalendarDays,
  ExternalLink,
  Flag,
  Gauge,
  MapPin,
  Trophy,
} from "lucide-react";

import { getHealth, getSchedule } from "./api/client";
import type { components } from "./api/schema";
import { MeetingDetails } from "./MeetingDetails";
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

function App() {
  const [viewState, setViewState] = useState<ViewState>("loading");
  const [meetings, setMeetings] = useState<Meeting[]>([]);
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
  const from = query.get("from") || "";
  const through = query.get("through") || "";
  const invalidDates = Boolean(from && through && from > through);
  const filtered = meetings.filter((meeting) => !invalidDates && (!competition || meeting.competition === competition)
    && (!circuit || meeting.circuit === circuit) && (!from || meeting.endDate >= from) && (!through || meeting.startDate <= through));
  const selectedId = query.get("meeting");
  const selected = meetings.find((meeting) => meeting.id === selectedId);

  useEffect(() => {
    let active = true;

    Promise.all([getHealth(), getSchedule()])
      .then(([health, schedule]) => {
        if (active) {
          setMeetings(schedule.meetings);
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
              {[...new Set(meetings.map((meeting) => meeting.competition))].sort().map((name) => <option key={name}>{name}</option>)}
            </select>
          </label>
          <label className="filter-field">
            <MapPin size={17} aria-hidden="true" />
            <select aria-label="Circuit" value={circuit} onChange={(event) => changeQuery("circuit", event.target.value)}>
              <option value="">All circuits</option>
              {[...new Set(meetings.map((meeting) => meeting.circuit))].sort().map((name) => <option key={name}>{name}</option>)}
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
        {viewState === "ready" && selected && <MeetingDetails meeting={selected} zone={query.get("zone") || "browser"} setZone={(zone) => changeQuery("zone", zone)} backHref={queryFor("meeting", "")} onBack={() => changeQuery("meeting", "")} />}
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
                <h2>No meetings published yet</h2>
                <p>The starting grid is clear for the first approved publication.</p>
              </div>
              <span className="empty-code">00</span>
            </div>
          )}

          {viewState === "ready" && meetings.length > 0 && (
            <div className="meeting-list">
              {filtered.map((meeting, index) => (
                <article className="meeting-row" key={meeting.id}>
                  <div className="meeting-round" aria-label={meeting.round ? `Round ${meeting.round}` : `Schedule position ${index + 1}`}>
                    {String(meeting.round || index + 1).padStart(2, "0")}
                  </div>
                  <div className="meeting-primary">
                    <p>{meeting.competition}</p>
                    <h2><a href={queryFor("meeting", meeting.id)} onClick={(event) => { if (!event.ctrlKey && !event.metaKey) { event.preventDefault(); changeQuery("meeting", meeting.id); } }}>{meeting.name}</a></h2>
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
      </main>

      <footer>
        <span>Local proof of concept</span>
        <span className="footer-rule" />
        <span>
          {viewState === "ready"
            ? meetings.length === 0
              ? "Awaiting first publication"
              : `${filtered.length} of ${meetings.length} meetings published`
            : "Service status"}
        </span>
      </footer>
    </div>
  );
}

export default App;