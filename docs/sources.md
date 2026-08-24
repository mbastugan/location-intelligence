# Data sources (MVP)

## Tier A — ingest first

| Source | What | Level | Access | Notes |
|--------|------|-------|--------|-------|
| [SERPAVI (MIVAU)](https://www.mivau.gob.es/vivienda/alquila-bien-es-tu-derecho/serpavi) | Habitual rent (€, €/m²) | Municipality (+ finer) | Excel download 2011–2024 | Tax-based, annual lag |
| [INE Indicadores Urbanos](https://www.ine.es/jaxiT3/Tabla.htm?t=69330) | Purchase €/m², crime rate | Mun. >20k | CSV `69330` | Notarial prices; crime per 1,000 |
| [Open-Meteo Archive](https://open-meteo.com/) | Mean annual temperature | Coordinates | Free HTTP API | Interim until AEMET key |

## Tier B — trends & access

| Source | What | Level | Notes |
|--------|------|-------|-------|
| MITMA valor tasado (via datos.gob / ISTAC) | €/m² time series | Province | Label as province, not city |
| [INE Padrón 29005](https://www.ine.es/jaxiT3/Tabla.htm?t=29005) | Municipal population | Municipality | CSV | Official 1 Jan figures |
| [OurAirports](https://ourairports.com/data/) | Airport coords / distance | Point | CSV | Nearest scheduled airport |

## Do not use as core

| Source | Why |
|--------|-----|
| Idealista scrape | ToS / legal / brittle; partner API is commercial |
| Fabricated metrics | Product trust dies |

## Provenance rule

Every `metric_observation` must store `source_id`, `period_start`, `collected_at`, and preferably `quality_flag`.
