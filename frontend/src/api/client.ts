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