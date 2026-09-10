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

  useEffect(() => {
    let active = true;

    Promise.all([getHealth(), getSchedule()])
      .then(([health, schedule]) => {
        if (active) {
          setMeetings(schedule.meetings);
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
        <a className="brand" href="/" aria-label="Motorsport Hub home">
          <span className="brand-mark" aria-hidden="true">
            <span />
            <span />
            <span />
          </span>
          <span>Motorsport Hub</span>
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
          <button type="button" disabled title="Competition filter">
            <Trophy size={17} aria-hidden="true" />
            <span>All competitions</span>
          </button>
          <button type="button" disabled title="Circuit filter">
            <MapPin size={17} aria-hidden="true" />
            <span>All circuits</span>
          </button>
          <button type="button" disabled title="Date filter">
            <CalendarDays size={17} aria-hidden="true" />
            <span>All dates</span>
          </button>
        </section>

        <section className="schedule-lane" aria-live="polite">
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
              {meetings.map((meeting, index) => (
                <article className="meeting-row" key={meeting.id}>
                  <div className="meeting-round" aria-label={`Schedule position ${index + 1}`}>
                    {String(index + 1).padStart(2, "0")}
                  </div>
                  <div className="meeting-primary">
                    <p>{meeting.competition}</p>
                    <h2>{meeting.name}</h2>
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
              : `${meetings.length} meeting published`
            : "Service status"}
        </span>
      </footer>
    </div>
  );
}

export default App;