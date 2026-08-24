import Link from "next/link";
import { notFound } from "next/navigation";
import { TrendChart } from "@/components/TrendChart";
import { formatValue, getCities, getCity } from "@/lib/data";

export async function generateStaticParams() {
  try {
    const cities = await getCities();
    return cities.map((c) => ({ city: c.slug }));
  } catch {
    return [{ city: "malaga" }, { city: "valencia" }, { city: "alicante" }];
  }
}

export default async function CityPage({
  params,
}: {
  params: Promise<{ city: string }>;
}) {
  const { city: slug } = await params;
  let data;
  try {
    data = await getCity(slug);
  } catch {
    notFound();
  }

  const others = ["malaga", "valencia", "alicante"].filter((s) => s !== slug);

  return (
    <>
      <p className="meta">
        {data.country.name} · INE code {data.admin_code ?? "—"}
      </p>
      <h1 className="page-title">{data.name}</h1>
      <p className="lede">
        Decision snapshot for living and investing. Values marked provisional are
        seed placeholders until official ETL replaces them.
      </p>

      <div className="score-row">
        {data.scores.map((score) => (
          <div key={score.code} className="score-card">
            <div className="label">{score.name}</div>
            <div className="value">{score.value.toFixed(1)}</div>
            {score.quality_flag !== "ok" ? (
              <span className="flag">{score.quality_flag}</span>
            ) : null}
          </div>
        ))}
      </div>

      <div className="actions" style={{ marginBottom: "1.25rem" }}>
        {others.map((other) => (
          <Link
            key={other}
            className="btn btn-secondary"
            href={`/compare/${slug}-vs-${other}`}
          >
            Compare vs {other}
          </Link>
        ))}
      </div>

      <section className="panel">
        <h2>Key metrics</h2>
        <table className="metrics">
          <thead>
            <tr>
              <th>Metric</th>
              <th>Value</th>
              <th>Period</th>
              <th>Source</th>
            </tr>
          </thead>
          <tbody>
            {data.metrics.map((m) => (
              <tr key={m.code}>
                <td>
                  {m.name}
                  {m.quality_flag !== "ok" ? (
                    <div className="flag">{m.quality_flag}</div>
                  ) : null}
                </td>
                <td className="num">
                  {formatValue(m.value, m.unit)}{" "}
                  <span className="meta">{m.unit}</span>
                </td>
                <td>{m.period_start}</td>
                <td className="meta">{m.source_code}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="panel">
        <TrendChart
          title="Property price history (€/m²)"
          series={data.series.property_price_m2 ?? []}
          unit="EUR/m2"
        />
      </section>

      <section className="panel">
        <TrendChart
          title="Rent history (€/m²/month, SERPAVI)"
          series={data.series.rent_m2 ?? []}
          unit="EUR/m2/month"
        />
      </section>
    </>
  );
}
