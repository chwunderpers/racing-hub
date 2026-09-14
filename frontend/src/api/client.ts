import type { components } from "./schema";

type HealthResponse = components["schemas"]["HealthResponse"];
type ScheduleResponse = components["schemas"]["ScheduleResponse"];

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "";

async function getJson<T>(path: string, acceptedStatuses = [200]): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`);
  if (!acceptedStatuses.includes(response.status)) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function getHealth(): Promise<HealthResponse> {
  return getJson<HealthResponse>("/api/health", [200, 503]);
}

export function getSchedule(): Promise<ScheduleResponse> {
  return getJson<ScheduleResponse>("/api/schedule");
}

export function getVehicles(): Promise<components["schemas"]["VehicleListResponse"]> {
  return getJson("/api/vehicles");
}

export function getVehicle(identity: string): Promise<components["schemas"]["VehicleDetailsResponse"] | null> {
  return getJson<components["schemas"]["VehicleDetailsResponse"] | { detail: string }>(`/api/vehicles/${encodeURIComponent(identity)}`, [200, 404])
    .then(result => "vehicle" in result ? result : null);
}

export function getCapabilities(subjectIri: string): Promise<components["schemas"]["CapabilityResponse"]> {
  return getJson(`/api/capabilities?${new URLSearchParams({ subjectIri })}`);
}

export function getExportSelection(): Promise<components["schemas"]["ExportSelection"]> {
  return getJson("/api/exports");
}

export async function downloadExport(version: string | null, format: "json" | "csv" | "turtle"): Promise<void> {
  const path = version ? `/api/exports/publications/${encodeURIComponent(version)}/${format}` : "/api/exports/ontology";
  const response = await fetch(`${apiBaseUrl}${path}`);
  if (response.status === 409) throw new Error("Publication changed. Refresh the publication before downloading.");
  if (!response.ok) throw new Error("Download unavailable. Retry the download.");
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement("a");
  link.href = url;
  link.download = version ? `racing-hub-${version}.${format === "turtle" ? "ttl" : format}` : "racing-hub-ontology.ttl";
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}