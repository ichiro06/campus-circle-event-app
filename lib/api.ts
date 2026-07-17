import type { CampusEvent, Circle } from "@/lib/campusData";

const API_BASE_URL = process.env.API_BASE_URL ?? "http://localhost:8000";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store" });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}

export function getCircles(): Promise<Circle[]> {
  return getJson<Circle[]>("/api/circles");
}

export function getEvents(): Promise<CampusEvent[]> {
  return getJson<CampusEvent[]>("/api/events");
}
