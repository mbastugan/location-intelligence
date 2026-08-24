import Link from "next/link";
import { SiteShell } from "@/components/SiteShell";
import { getCities } from "@/lib/data";

export default async function HomePage() {
  let cities: Awaited<ReturnType<typeof getCities>> = [];
  let error: string | null = null;
  try {
    cities = await getCities();
  } catch {
    error =
      "API is offline. Start the API or use static data mode for GitHub Pages.";
  }

  return (
    <SiteShell fullBleed>
      <section className="home-hero" aria-label="WhichPlaceGusto">
        <div className="home-hero__media" aria-hidden="true" />
        <div className="home-hero__content">
          <h1 className="home-hero__brand">WhichPlaceGusto</h1>
          <p className="home-hero__line">
            Decide where to live or invest with official city data — not listing
            spam.
          </p>
          <div className="actions">
            <Link className="btn btn-primary" href="/spain/malaga">
              Explore cities
            </Link>
            <Link className="btn btn-secondary" href="/compare/malaga-vs-alicante">
              Compare cities
            </Link>
          </div>
        </div>
      </section>

      <section className="home-cities">
        <h2 className="home-cities__head">Start with Spain</h2>
        {error ? <p className="alert">{error}</p> : null}
        <ul className="city-list">
          {cities.map((city) => (
            <li key={city.slug}>
              <Link href={`/spain/${city.slug}`}>
                <strong>{city.name}</strong>
                <span>Housing · rent · climate · scores</span>
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </SiteShell>
  );
}
