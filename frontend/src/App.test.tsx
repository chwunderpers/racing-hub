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


it("does not show the empty state when meetings are returned", async () => {
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const url = String(input);
    if (url.endsWith("/api/health")) {
      return Response.json({ status: "ok", database: "ok" });
    }
    return Response.json({ meetings: [{ id: "meeting-1" }] });
  });

  render(<App />);

  expect(await screen.findByText("Schedule update required")).toBeVisible();
  expect(screen.queryByText("No meetings published yet")).not.toBeInTheDocument();
});