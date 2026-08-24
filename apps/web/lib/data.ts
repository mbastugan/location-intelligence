import { promises as fs } from "fs";
import path from "path";

export type Metric = {
  code: string;
  name: string;
  unit: string;
  category: string;
  value: number;
  period_start: string;
  quality_flag: string;
  source_code: string;
  source_url: string | null;
  collected_at: string;
};

export type Score = {
  code: string;
  name: string;
  version: string;
  value: number;
  coverage: number;
  quality_flag: string;
  computed_at: string;
};

export type CityPayload = {
  slug: string;
  name: string;
  name_local: string | null;
  country: { iso2: string; name: string };
  admin_code: string | null;
  coordinates: { lat: number; lon: number };
  metrics: Metric[];
  series: Record<string, { period_start: string; value: number; quality_flag: string }[]>;
  scores: Score[];
};

export type CityIndexItem = {
  slug: string;
  name: string;
  name_local?: string | null;
  country?: { iso2: string; name: string };
  country_iso2?: string;
  path: string;
};

export type ComparePayload = {
  a: { slug: string; name: string };
  b: { slug: string; name: string };
  rows: { code: string; name: string; unit: string; a: number | null; b: number | null }[];
  insights: string[];
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";
const DATA_MODE = process.env.NEXT_PUBLIC_DATA_MODE ?? "api";

async function readStaticFile<T>(filename: string): Promise<T> {
  const filePath = path.join(process.cwd(), "public", "data", filename);
  const raw = await fs.readFile(filePath, "utf8");
  return JSON.parse(raw) as T;
}

export async function getCities(): Promise<CityIndexItem[]> {
  if (DATA_MODE === "static") {
    return readStaticFile<CityIndexItem[]>("cities.json");
  }
  const res = await fetch(`${API_BASE}/cities`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load cities");
  return res.json();
}

export async function getCity(slug: string): Promise<CityPayload> {
  if (DATA_MODE === "static") {
    return readStaticFile<CityPayload>(`city-${slug}.json`);
  }
  const res = await fetch(`${API_BASE}/cities/${slug}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`City not found: ${slug}`);
  return res.json();
}

export async function getCompare(pair: string): Promise<ComparePayload> {
  if (DATA_MODE === "static") {
    return readStaticFile<ComparePayload>(`compare-${pair}.json`);
  }
  const res = await fetch(`${API_BASE}/compare/${pair}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Compare not found: ${pair}`);
  return res.json();
}

export function formatValue(value: number | null, unit: string): string {
  if (value === null || Number.isNaN(value)) return "—";
  if (unit === "count") return Math.round(value).toLocaleString("en-GB");
  if (unit === "%" || unit === "score_0_100") return value.toFixed(1);
  if (unit.includes("EUR")) {
    return value.toLocaleString("en-GB", { maximumFractionDigits: 1 });
  }
  return value.toLocaleString("en-GB", { maximumFractionDigits: 1 });
}
