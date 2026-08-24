# Metric definitions (MVP)

Canonical codes used in `metric_definition.code`.

| Code | Name | Unit | Higher better? | Category |
|------|------|------|----------------|----------|
| property_price_m2 | Mean purchase price | EUR/m2 | no | property |
| rent_m2 | Mean rent | EUR/m2/month | no | property |
| estimated_gross_yield | Approx. gross rental yield | % | yes | property |
| population | Population | count | neutral | population |
| foreign_population_share | Foreign population share | % | neutral | population |
| avg_temp_annual | Mean annual temperature | C | neutral | weather |
| sunshine_hours_annual | Sunshine hours (annual) | hours | yes | weather |
| airport_distance_km | Nearest major airport | km | no | accessibility |
| living_score | Living score v1 | score_0_100 | yes | score |
| investment_score | Investment score v1 | score_0_100 | yes | score |

## Derived formulas

### estimated_gross_yield

```text
(rent_m2 * 12 / property_price_m2) * 100
```

Assumes rent and price refer to comparable stock. Mark as estimate.

### living_score / investment_score (v1)

Min-max normalize available input metrics across the MVP city set, apply weights from `score_weight`, scale to 0–100.
Missing inputs → factor skipped and score marked `partial` when coverage < 70%.

Weights live in the database / `pipeline/config/scores.yaml` — never hard-coded in React components.
