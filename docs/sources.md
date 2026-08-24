# Data sources (MVP)

## Tier A — ingest first

| Source | What | Level | Access | Notes |
|--------|------|-------|--------|-------|
| [SERPAVI (MIVAU)](https://www.mivau.gob.es/vivienda/alquila-bien-es-tu-derecho/serpavi) | Habitual rent (€, €/m²) | Municipality (+ finer) | Excel download 2011–2024 | Tax-based, annual lag |
| [INE Indicadores Urbanos](https://ine.es/dyngs/Prensa/UA2025.htm) | Purchase €/m², rent spend, foreigners, crime | City / mun. >20k | INEbase tables | Notarial prices from 2025 edition |
| [INE Padrón](https://www.ine.es/) | Population | Municipality | Open tables | Official |
| [AEMET OpenData](https://www.aemet.es/es/datos_abiertos/AEMET_OpenData) | Climate / weather | Station | Free API key | Map stations → cities |

## Tier B — trends & access

| Source | What | Level | Notes |
|--------|------|-------|-------|
| MITMA valor tasado (via datos.gob / ISTAC) | €/m² time series | Province | Label as province, not city |
| [OurAirports](https://ourairports.com/data/) | Airport coords | Point | Distance computed locally |
| INE Atlas de renta | Income | Municipality | Affordability inputs |

## Do not use as core

| Source | Why |
|--------|-----|
| Idealista scrape | ToS / legal / brittle; partner API is commercial |
| Fabricated metrics | Product trust dies |

## Provenance rule

Every `metric_observation` must store `source_id`, `period_start`, `collected_at`, and preferably `quality_flag`.
