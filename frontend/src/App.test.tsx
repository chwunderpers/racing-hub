import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";

import App from "./App";


afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
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
  expect(screen.getByText("No meetings published yet")).toBeVisible();
});


it("shows an unavailable state when the backend health check fails", async () => {
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


it("shows a published Formula One meeting with its provenance", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const url = String(input);
    if (url.endsWith("/api/health")) {
      return Response.json({ status: "ok", database: "ok" });
    }
    return Response.json({
      meetings: [
        {
          id: "meeting:f1:2026:australia",
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
  expect(screen.getByText("Formula One")).toBeVisible();
  expect(screen.getByText("Albert Park Grand Prix Circuit")).toBeVisible();
  expect(screen.getByText("6-8 March 2026")).toBeVisible();
  expect(screen.getByRole("link", { name: "Formula One source" })).toHaveAttribute(
    "href",
    "https://www.formula1.com/en/racing/2026/australia",
  );
  expect(screen.getByText("Retrieved 15 January 2026, 12:00 UTC")).toBeVisible();
  expect(screen.queryByText("No meetings published yet")).not.toBeInTheDocument();
});