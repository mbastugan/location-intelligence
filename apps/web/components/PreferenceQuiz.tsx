"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import type { CityPayload } from "@/lib/data";
import {
  defaultPreferences,
  rankCities,
  type Importance,
  type Preferences,
  type Purpose,
} from "@/lib/recommend";

const STEPS = ["purpose", "priorities", "results"] as const;

const IMPORTANCE_OPTIONS: { value: Importance; label: string }[] = [
  { value: "low", label: "Less important" },
  { value: "medium", label: "Somewhat" },
  { value: "high", label: "Very important" },
];

function compareHref(a: string, b: string): string {
  const order = ["malaga", "valencia", "alicante"];
  const ia = order.indexOf(a);
  const ib = order.indexOf(b);
  if (ia < 0 || ib < 0) return `/compare/${a}-vs-${b}`;
  return ia < ib ? `/compare/${a}-vs-${b}` : `/compare/${b}-vs-${a}`;
}

function basePath(): string {
  return process.env.NEXT_PUBLIC_BASE_PATH ?? "";
}

async function loadCities(): Promise<CityPayload[]> {
  const slugs = ["malaga", "valencia", "alicante"];
  const prefix = basePath();
  const payloads = await Promise.all(
    slugs.map(async (slug) => {
      const res = await fetch(`${prefix}/data/city-${slug}.json`, {
        cache: "no-store",
      });
      if (!res.ok) throw new Error(`Failed to load ${slug}`);
      return res.json() as Promise<CityPayload>;
    })
  );
  return payloads;
}

function ChoiceRow<T extends string>({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: T;
  options: { value: T; label: string }[];
  onChange: (value: T) => void;
}) {
  return (
    <fieldset className="quiz-field">
      <legend>{label}</legend>
      <div className="quiz-choices">
        {options.map((opt) => (
          <button
            key={opt.value}
            type="button"
            className={
              value === opt.value ? "quiz-choice is-active" : "quiz-choice"
            }
            onClick={() => onChange(opt.value)}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </fieldset>
  );
}

export function PreferenceQuiz() {
  const [step, setStep] = useState(0);
  const [prefs, setPrefs] = useState<Preferences>(defaultPreferences);
  const [cities, setCities] = useState<CityPayload[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const ranked = useMemo(() => {
    if (!cities) return [];
    return rankCities(cities, prefs);
  }, [cities, prefs]);

  async function goResults() {
    setLoading(true);
    setError(null);
    try {
      const data = cities ?? (await loadCities());
      setCities(data);
      setStep(2);
    } catch {
      setError("Could not load city data. Try again in a moment.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="quiz">
      <div className="quiz-progress" aria-hidden="true">
        {STEPS.map((name, index) => (
          <span
            key={name}
            className={index <= step ? "quiz-dot is-on" : "quiz-dot"}
          />
        ))}
      </div>

      {step === 0 ? (
        <section className="quiz-panel">
          <h2>What are you deciding?</h2>
          <p className="lede">
            A short preference check — not a chatbot. Your answers re-weight the
            same official metrics.
          </p>
          <ChoiceRow<Purpose>
            label="Primary goal"
            value={prefs.purpose}
            onChange={(purpose) => setPrefs((p) => ({ ...p, purpose }))}
            options={[
              { value: "live", label: "Live / relocate" },
              { value: "invest", label: "Invest" },
              { value: "both", label: "Both" },
            ]}
          />
          <div className="actions">
            <button
              type="button"
              className="btn btn-on-light btn-primary"
              onClick={() => setStep(1)}
            >
              Next
            </button>
          </div>
        </section>
      ) : null}

      {step === 1 ? (
        <section className="quiz-panel">
          <h2>What matters most?</h2>
          <p className="lede">
            Tell us how strongly each factor should influence the ranking.
          </p>
          <ChoiceRow<Importance>
            label="Affordability"
            value={prefs.affordability}
            onChange={(affordability) =>
              setPrefs((p) => ({ ...p, affordability }))
            }
            options={IMPORTANCE_OPTIONS}
          />
          {(prefs.purpose === "live" || prefs.purpose === "both") && (
            <>
              <ChoiceRow<Importance>
                label="Warm climate"
                value={prefs.climate}
                onChange={(climate) => setPrefs((p) => ({ ...p, climate }))}
                options={IMPORTANCE_OPTIONS}
              />
              <ChoiceRow<Importance>
                label="Close to airport"
                value={prefs.airport}
                onChange={(airport) => setPrefs((p) => ({ ...p, airport }))}
                options={IMPORTANCE_OPTIONS}
              />
              <ChoiceRow<Importance>
                label="Safety (lower crime)"
                value={prefs.safety}
                onChange={(safety) => setPrefs((p) => ({ ...p, safety }))}
                options={IMPORTANCE_OPTIONS}
              />
            </>
          )}
          {(prefs.purpose === "invest" || prefs.purpose === "both") && (
            <ChoiceRow<Importance>
              label="Rental yield"
              value={prefs.yieldFocus}
              onChange={(yieldFocus) => setPrefs((p) => ({ ...p, yieldFocus }))}
              options={IMPORTANCE_OPTIONS}
            />
          )}
          <div className="actions">
            <button
              type="button"
              className="btn btn-on-light btn-secondary"
              onClick={() => setStep(0)}
            >
              Back
            </button>
            <button
              type="button"
              className="btn btn-on-light btn-primary"
              onClick={() => void goResults()}
              disabled={loading}
            >
              {loading ? "Ranking…" : "See my ranking"}
            </button>
          </div>
          {error ? <p className="alert">{error}</p> : null}
        </section>
      ) : null}

      {step === 2 ? (
        <section className="quiz-panel">
          <h2>Your match ranking</h2>
          <p className="lede">
            Scores are preference-weighted from the current metric set for
            Málaga, Valencia, and Alicante.
          </p>
          <ol className="quiz-results">
            {ranked.map((city, index) => (
              <li key={city.slug}>
                <div className="quiz-result-top">
                  <span className="quiz-rank">#{index + 1}</span>
                  <strong>{city.name}</strong>
                  <span className="quiz-score">{city.score.toFixed(1)}</span>
                </div>
                {city.reasons.length ? (
                  <p className="meta">Strong on: {city.reasons.join(" · ")}</p>
                ) : null}
                <div className="actions" style={{ marginTop: "0.75rem" }}>
                  <Link
                    className="btn btn-on-light btn-secondary"
                    href={`/spain/${city.slug}`}
                  >
                    Open city
                  </Link>
                  {index === 0 && ranked[1] ? (
                    <Link
                      className="btn btn-on-light btn-primary"
                      href={compareHref(city.slug, ranked[1].slug)}
                    >
                      Compare with #{2}
                    </Link>
                  ) : null}
                </div>
              </li>
            ))}
          </ol>
          <div className="actions" style={{ marginTop: "1.5rem" }}>
            <button
              type="button"
              className="btn btn-on-light btn-secondary"
              onClick={() => setStep(1)}
            >
              Adjust preferences
            </button>
          </div>
        </section>
      ) : null}
    </div>
  );
}
