import { notFound } from "next/navigation";
import { formatValue, getCompare } from "@/lib/data";

export function generateStaticParams() {
  return [
    { pair: "malaga-vs-valencia" },
    { pair: "malaga-vs-alicante" },
    { pair: "valencia-vs-alicante" },
  ];
}

export default async function ComparePage({
  params,
}: {
  params: Promise<{ pair: string }>;
}) {
  const { pair } = await params;
  let data;
  try {
    data = await getCompare(pair);
  } catch {
    notFound();
  }

  return (
    <>
      <h1 className="page-title">
        {data.a.name} vs {data.b.name}
      </h1>
      <p className="lede">
        Side-by-side metrics with simple decision cues. Lower purchase/rent price
        and closer airport win when relevant; higher yield and scores win for
        investment/living.
      </p>

      <section className="panel">
        <h2>Insights</h2>
        <ul className="insights">
          {data.insights.map((insight) => (
            <li key={insight}>{insight}</li>
          ))}
        </ul>
      </section>

      <section className="panel">
        <h2>Comparison</h2>
        <table className="metrics">
          <thead>
            <tr>
              <th>Metric</th>
              <th className="num">{data.a.name}</th>
              <th className="num">{data.b.name}</th>
            </tr>
          </thead>
          <tbody>
            {data.rows.map((row) => (
              <tr key={row.code}>
                <td>
                  {row.name}
                  <div className="meta">{row.unit}</div>
                </td>
                <td className="num">{formatValue(row.a, row.unit)}</td>
                <td className="num">{formatValue(row.b, row.unit)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
