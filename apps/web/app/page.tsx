import Link from "next/link";
import { getCities } from "@/lib/data";

export default async function HomePage() {
  let cities: Awaited<ReturnType<typeof getCities>> = [];
  let error: string | null = null;
  try {
    cities = await getCities();
  } catch {
    error =
      "API is offline. Start the API (`uvicorn apps.api.main:app --reload --port 8000`) or switch to static data mode.";
  }

  return (
    <>
      <section className="hero">
        <h1>WhichPlaceGusto</h1>
        <p>
          Find the best place to live or invest using real data — not listing
          spam. Compare Spanish cities on housing, rent, climate, and access.
        </p>
        <div className="actions">
          <Link className="btn btn-primary" href="/spain/malaga">
            Explore cities
          </Link>
          <Link className="btn btn-secondary" href="/compare/malaga-vs-alicante">
            Compare cities
          </Link>
        </div>
      </section>

      {error ? <p className="meta">{error}</p> : null}

      <div className="city-grid">
        {cities.map((city) => (
          <Link key={city.slug} className="city-link" href={`/spain/${city.slug}`}>
            <strong>{city.name}</strong>
            <span>Spain · metrics, scores, trends</span>
          </Link>
        ))}
      </div>
    </>
  );
}
