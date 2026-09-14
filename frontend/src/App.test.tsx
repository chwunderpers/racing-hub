import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";

import App from "./App";


afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  window.history.replaceState({}, "", "/");
});

it("opens vehicle details separately from schedule filters and retains field provenance", async () => {
  const assertion = { iri: "https://example.test/assertion", value: "GT racing car", applicability: "Descriptive model only", evidenceKind: "secondary", publisher: "Wikipedia", sourceUrl: "https://en.wikipedia.org/wiki/Fixture", retrievedAt: "2026-09-14T08:00:00Z", checksum: "a".repeat(64), anchor: "Model overview" };
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const url = String(input);
    if (url.endsWith("/api/health")) return Response.json({ status: "ok", database: "ok" });
    if (url.endsWith("/api/vehicles")) return Response.json({ publicationVersion: "test", vehicles: [{ identity: "fixture:model", iri: "https://example.test/model", title: "Fixture GT" }] });
    if (url.endsWith("/api/vehicles/fixture%3Amodel")) return Response.json({ publicationVersion: "test", vehicle: { iri: "https://example.test/model", title: "Fixture GT", eligibilityEstablished: false, fields: [{ field: "category", value: "GT racing car", conflict: false, assertions: [assertion] }] } });
    return Response.json({ meetings: [] });
  });
  render(<App />);
  await screen.findByText("System ready");
  fireEvent.click(screen.getByRole("link", { name: "Vehicles" }));
  expect(screen.queryByRole("region", { name: "Schedule filters" })).not.toBeInTheDocument();
  fireEvent.click(await screen.findByRole("link", { name: "Fixture GT" }));
  expect(await screen.findByRole("heading", { name: "Fixture GT" })).toBeVisible();
  expect(screen.getByText(/Competition Eligibility is not established/)).toBeVisible();
  fireEvent.click(screen.getByText("Evidence (1)"));
  expect(screen.getByText("Secondary Evidence")).toBeVisible();
  expect(screen.getByText("Descriptive model only")).toBeVisible();
  expect(screen.getByRole("link", { name: "Wikipedia" })).toHaveAttribute("href", assertion.sourceUrl);
  expect(screen.queryByText("Power")).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("link", { name: "Schedule" }));
  expect(screen.getByRole("region", { name: "Schedule filters" })).toBeVisible();
});

it.each(["empty", "missing", "unavailable"])("shows the %s vehicle state without schedule filters", async state => {
  window.history.replaceState({}, "", state === "missing" ? "/?view=vehicles&vehicle=unknown" : "/?view=vehicles");
  vi.spyOn(globalThis, "fetch").mockImplementation(async input => {
    const url = String(input);
    if (url.includes("/api/vehicles")) return state === "unavailable" ? new Response(null, { status: 503 }) : state === "missing" ? Response.json({ detail: "Not found" }, { status: 404 }) : Response.json({ publicationVersion: null, vehicles: [] });
    return Response.json(url.endsWith("/api/health") ? { status: "ok", database: "ok" } : { meetings: [] });
  });
  render(<App />);
  expect(await screen.findByRole("heading", { name: state === "empty" ? "No vehicles published yet" : state === "missing" ? "Vehicle not found" : "Vehicle service unavailable" })).toBeVisible();
  expect(screen.queryByRole("region", { name: "Schedule filters" })).not.toBeInTheDocument();
  if (state === "unavailable") expect(screen.getByRole("button", { name: "Retry" })).toBeVisible();
});


it("shows a ready empty schedule when the backend is healthy", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const url = String(input);
    if (url.endsWith("/api/health")) {
      return Response.json({ status: "ok", database: "ok" });
    }
    return Response.json({ meetings: [] });
  });

  render(<App />);

  expect(await screen.findByText("System ready")).toBeVisible();
  expect(screen.getByRole("link", { name: "Racing Hub home" })).toHaveTextContent("Racing Hub");
  expect(screen.getByText("No meetings published yet")).toBeVisible();
});


it.each(["/", "/?meeting=missing"])("shows an unavailable state at %s when the backend health check fails", async (url) => {
  window.history.replaceState({}, "", url);
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const url = String(input);
    if (url.endsWith("/api/health")) {
      return Response.json(
        { status: "degraded", database: "unavailable" },
        { status: 503 },
      );
    }
    return Response.json({ meetings: [] });
  });

  render(<App />);

  expect(await screen.findByText("Database unavailable")).toBeVisible();
  expect(screen.getByText("Schedule service unavailable")).toBeVisible();
});


it.each(["scheduled", "cancelled"])("shows a %s Formula One meeting with its provenance", async (status) => {
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const url = String(input);
    if (url.endsWith("/api/health")) {
      return Response.json({ status: "ok", database: "ok" });
    }
    return Response.json({
      meetings: [
        {
          id: "meeting:f1:2026:australia",
          status,
          name: "Australian Grand Prix",
          competition: "Formula One",
          season: 2026,
          circuit: "Albert Park Grand Prix Circuit",
          startDate: "2026-03-06",
          endDate: "2026-03-08",
          sourceUrl: "https://www.formula1.com/en/racing/2026/australia",
          retrievedAt: "2026-01-15T12:00:00Z",
        },
      ],
    });
  });

  render(<App />);

  expect(await screen.findByText("Australian Grand Prix")).toBeVisible();
  expect(screen.getAllByText("Formula One").some((element) => element.tagName === "P")).toBe(true);
  expect(screen.getAllByText("Albert Park Grand Prix Circuit").some((element) => element.tagName === "SPAN")).toBe(true);
  expect(screen.getByText("6-8 March 2026")).toBeVisible();
  expect(screen.getByRole("link", { name: "Formula One source" })).toHaveAttribute(
    "href",
    "https://www.formula1.com/en/racing/2026/australia",
  );
  expect(screen.getByText("Retrieved 15 January 2026, 12:00 UTC")).toBeVisible();
  expect(screen.queryByText("No meetings published yet")).not.toBeInTheDocument();
  if (status === "cancelled") {
    expect(screen.getByText("Cancelled")).toBeVisible();
  } else {
    expect(screen.queryByText("Cancelled")).not.toBeInTheDocument();
  }
});

it.each(["/", "/?from=2026-2-01", "/?from=2026-02-30"])("preserves filters through details and displays resolved and unresolved session times at %s", async (url) => {
  window.history.replaceState({}, "", url);
  const meeting = {
    id: "meeting:australia", name: "Australian Grand Prix", competition: "Formula One",
    circuit: "Albert Park", season: 2026, status: "scheduled", round: 1,
    startDate: "2026-03-06", endDate: "2026-03-08", eventTimezone: "Australia/Melbourne",
    sourceUrl: "https://www.formula1.com/en/racing/2026/australia", retrievedAt: "2026-09-10T08:00:00Z",
    sessions: [
      { id: "p1", name: "Practice 1", status: "completed", start: { local: "2026-03-06T12:30:00", instant: "2026-03-06T01:30:00Z", zone: "Australia/Melbourne", offset: "+11:00" }, end: null },
      { id: "q", name: "Qualifying", status: "scheduled", start: { local: "2026-03-07", instant: null, zone: null, offset: null }, end: null },
    ],
  };
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => Response.json(String(input).endsWith("/api/health")
    ? { status: "ok", database: "ok" }
    : { meetings: [meeting, { ...meeting, id: "china", name: "Chinese Grand Prix", circuit: "Shanghai", startDate: "2026-03-13", endDate: "2026-03-15" }], freshness: { stale: true, reason: "Source fetch failed" } }));
  render(<App />);
  await screen.findByText("System ready");
  expect(screen.getByText(/Schedule may be outdated/)).toBeVisible();
  if (url !== "/") {
    expect(screen.getByRole("alert")).toHaveTextContent("Date filters must use valid YYYY-MM-DD dates");
    expect(screen.getByRole("link", { name: "Australian Grand Prix" })).toBeVisible();
    fireEvent.change(screen.getByLabelText("From date"), { target: { value: "2026-03-06" } });
  }
  fireEvent.change(screen.getByRole("combobox", { name: "Competition" }), { target: { value: "Formula One" } });
  fireEvent.change(screen.getByLabelText("Through date"), { target: { value: "2026-03-08" } });
  expect(screen.queryByText("Chinese Grand Prix")).not.toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("From date"), { target: { value: "2026-03-09" } });
  expect(screen.getByRole("alert")).toHaveTextContent("From date must not follow");
  fireEvent.change(screen.getByLabelText("From date"), { target: { value: "2026-03-06" } });
  fireEvent.change(screen.getByRole("combobox", { name: "Circuit" }), { target: { value: "Albert Park" } });
  expect(screen.queryByText("Chinese Grand Prix")).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("link", { name: "Australian Grand Prix" }));
  fireEvent.change(screen.getByRole("combobox", { name: "Display time zone" }), { target: { value: "UTC" } });
  expect(screen.getByText(/01:30:00/)).toBeVisible();
  expect(screen.getByText("2026-03-07 (unresolved)")).toBeVisible();
  fireEvent.change(screen.getByRole("combobox", { name: "Display time zone" }), { target: { value: "event" } });
  expect(screen.getByText(/12:30:00/, { selector: "time" })).toBeVisible();
  fireEvent.change(screen.getByRole("combobox", { name: "Display time zone" }), { target: { value: "America/New_York" } });
  expect(screen.getByText(/20:30:00/, { selector: "time" })).toHaveTextContent("5 Mar 2026");
  fireEvent.click(screen.getByRole("link", { name: "Back to schedule" }));
  expect(screen.getByRole("combobox", { name: "Circuit" })).toHaveValue("Albert Park");
  expect(screen.queryByText("Chinese Grand Prix")).not.toBeInTheDocument();
  expect(window.location.search).toContain("circuit=Albert+Park");
  expect(screen.getByLabelText("From date")).toHaveValue("2026-03-06");
  expect(screen.getByLabelText("Through date")).toHaveValue("2026-03-08");
});

it("filters shared Circuits by identity and navigates across Competitions without numbering prologues", async () => {
  const common = { season: 2026, status: "scheduled", startDate: "2026-05-19", endDate: "2026-05-20", retrievedAt: "2026-09-10T09:47:31Z", publicationVersion: "test", sessions: [] };
  const meetings = [
    { ...common, id: "f1-spa", name: "Belgian Grand Prix", competition: "Formula One", competitionId: "competition:formula-one", circuit: "Circuit de Spa-Francorchamps", circuitId: "circuit:f1-circuit-7", round: 12, kind: "championship", sourceUrl: "https://www.formula1.com/en/racing/2026/belgium" },
    { ...common, id: "gt-spa", name: "Spa Prologue", competition: "GT World Challenge Europe", competitionId: "competition:gt-world-challenge-europe", circuit: "Spa-Francorchamps", circuitId: "circuit:f1-circuit-7", round: null, roundId: null, kind: "prologue", sourceUrl: "https://www.gt-world-challenge-europe.com/event/245/crowdstrike-24-hours-of-spa--test-days", fieldAssertions: [{ field: "kind", value: "Round 3", source_url: "https://www.gt-world-challenge-europe.com/calendar", retrieved_at: "2026-09-10T09:47:31Z", locator: "Event.description", rule: "Calendar classification takes precedence", preferred: false }] },
    { ...common, id: "other", name: "Different circuit", competition: "GT World Challenge Europe", competitionId: "competition:gt-world-challenge-europe", circuit: "Spa-Francorchamps", circuitId: "circuit:unrelated", round: 2, sourceUrl: "https://www.gt-world-challenge-europe.com/calendar" },
  ];
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => Response.json(String(input).endsWith("/api/health") ? { status: "ok", database: "ok" } : { meetings }));
  render(<App />);
  await screen.findByText("System ready");
  fireEvent.change(screen.getByRole("combobox", { name: "Circuit" }), { target: { value: "circuit:f1-circuit-7" } });
  expect(screen.getByRole("link", { name: "Belgian Grand Prix" })).toBeVisible();
  expect(screen.getByRole("link", { name: "Spa Prologue" })).toBeVisible();
  expect(screen.queryByRole("link", { name: "Different circuit" })).not.toBeInTheDocument();
  const row = screen.getByRole("link", { name: "Spa Prologue" }).closest("article")!;
  expect(within(row).getByLabelText("Prologue")).toBeVisible();
  expect(within(row).queryByLabelText(/Round|Schedule position/)).not.toBeInTheDocument();
  fireEvent.change(screen.getByRole("combobox", { name: "Competition" }), { target: { value: "competition:formula-one" } });
  fireEvent.click(screen.getByRole("link", { name: "Belgian Grand Prix" }));
  const related = screen.getByRole("region", { name: "Shared circuit" });
  fireEvent.click(within(related).getByRole("link", { name: /Spa Prologue/ }));
  expect(screen.getByRole("heading", { name: "Spa Prologue" })).toBeVisible();
  fireEvent.click(screen.getByText("Source assertions (1)"));
  expect(screen.getByText("Round 3")).toBeVisible();
  expect(screen.getByText("Event.description")).toBeVisible();
  fireEvent.click(screen.getByRole("link", { name: "Back to schedule" }));
  expect(screen.getByRole("combobox", { name: "Circuit" })).toHaveValue("circuit:f1-circuit-7");
  expect(screen.getByRole("combobox", { name: "Competition" })).toHaveValue("competition:formula-one");
});

it.each([
  ["complete", "empty", "Officially empty schedule"],
  ["incomplete", "unknown", "Coverage incomplete"],
  ["unassessed", "unknown", "Coverage unassessed"],
])("distinguishes %s coverage from absence of published Meetings", async (state, activity, label) => {
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => Response.json(String(input).endsWith("/api/health")
    ? { status: "ok", database: "ok" }
    : { meetings: [], coverage: [{ competitionId: "competition:nls", season: 2026, state, activity, reason: "Official source assessment", source_url: "https://example.org/calendar" }] }));
  render(<App />);
  await screen.findByText("System ready");
  expect(screen.getByText(label)).toBeVisible();
  expect(screen.queryByText("No meetings published yet")).not.toBeInTheDocument();
  expect(screen.queryByText("Awaiting first publication")).not.toBeInTheDocument();
  expect(screen.queryByText("The starting grid is clear for the first approved publication.")).not.toBeInTheDocument();
});

it("shows multi-Round NLS details with abandonment, nominal duration, place and incomplete clocks", async () => {
  window.history.replaceState({}, "", "/?meeting=nls-qualifiers");
  const meeting = {
    id: "nls-qualifiers", name: "NLS Qualifiers", competition: "NLS", competitionId: "competition:nls", season: 2026,
    circuit: "Nordschleife combined course", circuitId: "circuit:nls:nordschleife-combined", status: "scheduled", kind: "championship",
    startDate: "2026-04-17", endDate: "2026-04-19", sourceUrl: "https://example.org/qualifiers", retrievedAt: "2026-09-10T11:00:00Z", publicationVersion: "test",
    venue: { identity: "nuerburgring", name: "Nuerburgring" }, layout: { identity: "qualifiers-2026", name: "Qualifiers route 2026", length_km: 25.378 },
    rounds: [{ id: "nls4", number: 4, name: "First race", status: "abandoned" }, { id: "nls5", number: 5, name: "Second race", status: "scheduled" }],
    coverage: { state: "incomplete", activity: "present", reason: "Friday timetable unverified", source_url: "https://example.org/qualifiers" },
    sessions: [{ id: "nls4-race", name: "Race", roundId: "nls4", status: "abandoned", durationMinutes: 240, start: { local: "2026-04-18T17:30", instant: null, zone: null, offset: null }, end: null }],
  };
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => Response.json(String(input).endsWith("/api/health") ? { status: "ok", database: "ok" } : { meetings: [meeting] }));
  render(<App />);
  await screen.findByText("System ready");
  expect(screen.getByText("Round 4: First race")).toBeVisible();
  expect(screen.getByText("Round 5: Second race")).toBeVisible();
  expect(screen.getByText("Nominal duration: 240 minutes")).toBeVisible();
  expect(screen.getByText("Scheduled end unknown")).toBeVisible();
  expect(screen.getByText("Qualifiers route 2026 / 25.378 km")).toBeVisible();
  expect(screen.getByText("Coverage incomplete: Friday timetable unverified")).toBeVisible();
  expect(screen.getAllByText("abandoned").length).toBeGreaterThan(0);
});