import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { AssistantChat } from "./AssistantChat";

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

it("renders synthetic contributions separately without source citations", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(Response.json({ sessionToken: "synthetic-session", available: true }))
    .mockResolvedValueOnce(Response.json({ text: "Synthetic data is not sporting evidence.", displayTimeZone: "UTC", classification: "unsupported", freshness: { stale: false }, citations: [], contributions: [{ id: "sample", title: "Synthetic Meeting note", subjectIri: "https://w3id.org/motorsport-hub/resource/meeting/sample", text: "Demonstration marker: A-01.", kind: "synthetic" }] }))
    .mockResolvedValue(new Response(null, { status: 204 }));
  render(<AssistantChat zone="UTC" setZone={() => {}} />);
  fireEvent.change(screen.getByRole("textbox", { name: "Question" }), { target: { value: "Show the synthetic note" } });
  await waitFor(() => expect(screen.getByRole("button", { name: "Send question" })).toBeEnabled());
  fireEvent.click(screen.getByRole("button", { name: "Send question" }));
  expect(await screen.findByText("Demonstration marker: A-01.")).toBeVisible();
  expect(screen.getByText("Synthetic data / Not sporting evidence")).toBeVisible();
  expect(screen.queryByRole("link")).not.toBeInTheDocument();
});

it("answers with source and display zone, then resets ephemeral context", async () => {
  const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(new Response(JSON.stringify({ sessionToken: "first-session", available: true })))
    .mockResolvedValueOnce(new Response(JSON.stringify({ text: "Australian Meeting: 6-8 March 2026.", displayTimeZone: "UTC", publicationVersion: "a".repeat(64), classification: "stated", freshness: { stale: false }, citations: [{ id: "citation-1", iri: "https://w3id.org/motorsport-hub/resource/meeting/australia", title: "Australian Grand Prix", sourceUrl: "https://www.formula1.com/en/racing/2026/australia", retrievedAt: "2026-09-10T08:00:00Z" }] })))
    .mockResolvedValueOnce(new Response(null, { status: 204 }))
    .mockResolvedValueOnce(new Response(JSON.stringify({ sessionToken: "second-session", available: true })));
  render(<AssistantChat zone="UTC" setZone={() => {}} />);
  await waitFor(() => expect(screen.getByRole("button", { name: "Send question" })).toBeDisabled());
  fireEvent.change(screen.getByRole("textbox", { name: "Question" }), { target: { value: "When is Australia?" } });
  await waitFor(() => expect(screen.getByRole("button", { name: "Send question" })).toBeEnabled());
  fireEvent.click(screen.getByRole("button", { name: "Send question" }));
  expect(await screen.findByText("Australian Meeting: 6-8 March 2026.")).toBeVisible();
  expect(screen.getByRole("link", { name: "Australian Grand Prix" })).toHaveAttribute("href", "https://www.formula1.com/en/racing/2026/australia");
  expect(screen.getByText("Display time zone: UTC")).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "New conversation" }));
  await waitFor(() => expect(screen.queryByText("Australian Meeting: 6-8 March 2026.")).not.toBeInTheDocument());
  expect(fetchMock.mock.calls[1][1]?.headers).toMatchObject({ "X-Assistant-Session": "first-session" });
  expect(localStorage.getItem("assistantSession")).toBeNull();
  expect(sessionStorage.getItem("assistantSession")).toBeNull();
});

it("submits structured comparison scope and keeps chat requests separate", async () => {
  const requests: Record<string, unknown>[] = [];
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input, options) => {
    if (String(input).endsWith("/sessions")) return new Response(JSON.stringify({ sessionToken: "comparison-session", available: true }));
    if (options?.method === "DELETE") return new Response(null, { status: 204 });
    requests.push(JSON.parse(String(options?.body)));
    return new Response(JSON.stringify({ text: "NLS reviewed evidence is unavailable.", displayTimeZone: "UTC", classification: "unsupported", freshness: { stale: false }, citations: [] }));
  });
  render(<AssistantChat zone="UTC" setZone={() => {}} />);
  fireEvent.click(screen.getByRole("radio", { name: "Compare rules" }));
  fireEvent.change(screen.getByLabelText("Season"), { target: { value: "2025" } });
  fireEvent.change(screen.getByLabelText("Topic"), { target: { value: "tyres" } });
  fireEvent.change(screen.getByLabelText("On date (optional)"), { target: { value: "2025-08-01" } });
  await waitFor(() => expect(screen.getByRole("button", { name: "Compare rules" })).toBeEnabled());
  expect(screen.queryByRole("textbox", { name: "Question" })).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Compare rules" }));
  expect(await screen.findByText("NLS reviewed evidence is unavailable.")).toBeVisible();
  expect(requests[0]).toMatchObject({ comparison: { season: 2025, topic: "tyres", on_date: "2025-08-01" } });
  fireEvent.click(screen.getByRole("radio", { name: "Chat" }));
  fireEvent.change(screen.getByRole("textbox", { name: "Question" }), { target: { value: "When is Australia?" } });
  fireEvent.click(screen.getByRole("button", { name: "Send question" }));
  await waitFor(() => expect(requests).toHaveLength(2));
  expect(requests[1]).not.toHaveProperty("comparison");
});