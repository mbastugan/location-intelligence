import type { CityPayload } from "@/lib/data";

export type Purpose = "live" | "invest" | "both";
export type Importance = "low" | "medium" | "high";

export type Preferences = {
  purpose: Purpose;
  affordability: Importance;
  climate: Importance;
  airport: Importance;
  safety: Importance;
  yieldFocus: Importance;
};

export type RankedCity = {
  slug: string;
  name: string;
  score: number;
  reasons: string[];
};

const IMP: Record<Importance, number> = {
  low: 0.35,
  medium: 1,
  high: 1.75,
};

function metricMap(city: CityPayload): Record<string, number> {
  return Object.fromEntries(city.metrics.map((m) => [m.code, m.value]));
}

function normalize(
  values: Record<string, number>,
  higherIsBetter: boolean
): Record<string, number> {
  const nums = Object.values(values);
  if (!nums.length) return {};
  const lo = Math.min(...nums);
  const hi = Math.max(...nums);
  if (hi === lo) {
    return Object.fromEntries(Object.keys(values).map((k) => [k, 0.5]));
  }
  return Object.fromEntries(
    Object.entries(values).map(([k, v]) => {
      const n = (v - lo) / (hi - lo);
      return [k, higherIsBetter ? n : 1 - n];
    })
  );
}

export function rankCities(
  cities: CityPayload[],
  prefs: Preferences
): RankedCity[] {
  const bySlug = Object.fromEntries(cities.map((c) => [c.slug, metricMap(c)]));

  const factors: {
    code: string;
    higher: boolean;
    weight: number;
    label: string;
  }[] = [];

  if (prefs.purpose === "live" || prefs.purpose === "both") {
    factors.push({
      code: "property_price_m2",
      higher: false,
      weight: IMP[prefs.affordability] * 1.1,
      label: "more affordable purchase price",
    });
    factors.push({
      code: "rent_m2",
      higher: false,
      weight: IMP[prefs.affordability],
      label: "more affordable rent",
    });
    factors.push({
      code: "avg_temp_annual",
      higher: true,
      weight: IMP[prefs.climate],
      label: "warmer climate",
    });
    factors.push({
      code: "airport_distance_km",
      higher: false,
      weight: IMP[prefs.airport],
      label: "closer airport",
    });
    factors.push({
      code: "crime_rate_per_1000",
      higher: false,
      weight: IMP[prefs.safety],
      label: "lower crime rate",
    });
  }

  if (prefs.purpose === "invest" || prefs.purpose === "both") {
    factors.push({
      code: "estimated_gross_yield",
      higher: true,
      weight: IMP[prefs.yieldFocus] * 1.2,
      label: "higher estimated yield",
    });
    factors.push({
      code: "property_price_m2",
      higher: false,
      weight: IMP[prefs.affordability] * 0.7,
      label: "lower entry price",
    });
    factors.push({
      code: "population",
      higher: true,
      weight: 0.45,
      label: "larger population base",
    });
  }

  const norms: Record<string, Record<string, number>> = {};
  for (const factor of factors) {
    const raw: Record<string, number> = {};
    for (const city of cities) {
      const value = bySlug[city.slug][factor.code];
      if (value !== undefined) raw[city.slug] = value;
    }
    norms[factor.code + ":" + factor.higher] = normalize(raw, factor.higher);
  }

  const ranked = cities.map((city) => {
    let weighted = 0;
    let total = 0;
    const reasonScores: { label: string; score: number }[] = [];

    for (const factor of factors) {
      const key = factor.code + ":" + factor.higher;
      const n = norms[key][city.slug];
      if (n === undefined) continue;
      weighted += n * factor.weight;
      total += factor.weight;
      reasonScores.push({ label: factor.label, score: n });
    }

    const score = total ? (100 * weighted) / total : 0;
    const reasons = reasonScores
      .sort((a, b) => b.score - a.score)
      .slice(0, 3)
      .filter((r) => r.score >= 0.55)
      .map((r) => r.label);

    return {
      slug: city.slug,
      name: city.name,
      score: Math.round(score * 10) / 10,
      reasons,
    };
  });

  return ranked.sort((a, b) => b.score - a.score);
}

export const defaultPreferences = (): Preferences => ({
  purpose: "both",
  affordability: "high",
  climate: "medium",
  airport: "medium",
  safety: "medium",
  yieldFocus: "medium",
});
