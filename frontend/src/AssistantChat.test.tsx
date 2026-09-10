import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { AssistantChat } from "./AssistantChat";

afterEach(() => vi.restoreAllMocks());

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