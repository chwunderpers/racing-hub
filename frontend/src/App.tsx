import { useEffect, useState } from "react";
import {
  Activity,
  CalendarDays,
  Flag,
  Gauge,
  MapPin,
  Trophy,
} from "lucide-react";

import { getHealth, getSchedule } from "./api/client";
import "./styles.css";

type ViewState =
  | "loading"
  | "ready"
  | "unsupported-schedule"
  | "database-unavailable"
  | "unavailable";

function App() {
  const [viewState, setViewState] = useState<ViewState>("loading");

  useEffect(() => {
    let active = true;

    Promise.all([getHealth(), getSchedule()])
      .then(([health, schedule]) => {
        if (active) {
          setViewState(
            health.status !== "ok"
              ? "database-unavailable"
              : schedule.meetings.length === 0
                ? "ready"
                : "unsupported-schedule",
          );
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
            {viewState === "unsupported-schedule" && "Schedule update required"}
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

          {viewState === "ready" && (
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

          {viewState === "unsupported-schedule" && (
            <div className="failure-state">
              <div className="failure-light" aria-hidden="true" />
              <div>
                <h2>Published schedule unavailable</h2>
                <p>This application version cannot display published meetings.</p>
              </div>
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
        <span>{viewState === "ready" ? "Awaiting first publication" : "Service status"}</span>
      </footer>
    </div>
  );
}

export default App;