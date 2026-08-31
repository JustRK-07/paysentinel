/**
 * API client — talks to the FastAPI service when available, falls back to mock data.
 */

import { mockKpis, mockCatalog, mockIterations, mockScoreStream, mockRecentAttacks, mockAtlasHeatmap, mockLiveScoring } from "./mock-data";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
const IDENTIFY_API = process.env.NEXT_PUBLIC_IDENTIFY_API || "http://localhost:8001";

export type Attack = {
  id: string;
  name: string;
  surface: string;
  severity: string;
  likelihood: string;
  mechanics: string;
  indicators: string[];
  suggested_defense: string[];
  ai_brief?: string;
};

export async function fetchKpis(): Promise<typeof mockKpis> {
  try {
    const r = await fetch(`${API_BASE}/metrics`, { cache: "no-store" });
    if (!r.ok) throw new Error("bad");
    return await r.json();
  } catch {
    return mockKpis;
  }
}

export async function fetchCatalog(): Promise<Attack[]> {
  try {
    const r = await fetch(`${IDENTIFY_API}/catalog`, { cache: "no-store" });
    if (!r.ok) throw new Error("bad");
    const j = await r.json();
    return j.items;
  } catch {
    return mockCatalog;
  }
}

export async function fetchAttack(id: string): Promise<Attack | null> {
  try {
    const r = await fetch(`${IDENTIFY_API}/catalog/${id}`, { cache: "no-store" });
    if (!r.ok) throw new Error("bad");
    return await r.json();
  } catch {
    return mockCatalog.find((a) => a.id === id) || null;
  }
}

export async function fetchAtlasHeatmap() {
  try {
    const r = await fetch(`${IDENTIFY_API}/analytics/heatmap`, { cache: "no-store" });
    if (!r.ok) throw new Error("bad");
    return (await r.json()).matrix;
  } catch {
    return mockAtlasHeatmap;
  }
}

export async function fetchIterations() {
  try {
    const r = await fetch(`${API_BASE}/metrics/loop`, { cache: "no-store" });
    if (!r.ok) throw new Error("bad");
    return await r.json();
  } catch {
    return mockIterations;
  }
}

export async function fetchLiveScoring() {
  try {
    const r = await fetch(`${API_BASE}/score/recent`, { cache: "no-store" });
    if (!r.ok) throw new Error("bad");
    return await r.json();
  } catch {
    return mockLiveScoring;
  }
}

export async function postScore(transactions: object[]) {
  const r = await fetch(`${API_BASE}/score`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ transactions }),
  });
  if (!r.ok) throw new Error("score failed");
  return await r.json();
}

export async function postScoreText(artifacts: object[]) {
  const r = await fetch(`${API_BASE}/score/text`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ artifacts }),
  });
  if (!r.ok) throw new Error("score_text failed");
  return await r.json();
}
