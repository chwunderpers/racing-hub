import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";

import App from "./App";


afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  window.history.replaceState({}, "", "/");
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

it("preserves filters through details and displays resolved and unresolved session times", async () => {
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