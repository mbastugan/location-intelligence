# Location Intelligence

Local-first **location decision engine** for comparing cities to live or invest in.
MVP focus: **Málaga, Valencia, Alicante** (Spain). Architecture is country-agnostic.

## Stack

| Layer | Choice | Why |
|-------|--------|-----|
| DB | SQLite (local MVP) | Zero install on Windows; swap to PostgreSQL later |
| ETL | Python | Open-data clients + reproducible metrics |
| API | FastAPI | Same language as ETL; clean contract for the UI |
| Web | Next.js (App Router) | City/compare pages + future SEO |
| Charts | ECharts | Via `echarts-for-react` |

## Repo layout

```text
apps/api          FastAPI
apps/web          Next.js
pipeline          ETL + seed + JSON export
db                Schema SQL
data              Local SQLite + raw dumps + static exports
docs              Metric / source notes
scripts           Dev helpers
```

## Quick start (Windows)

### 1. Python API + database

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pipeline.jobs.init_db
# Optional: after downloading SERPAVI Excel into data/raw/serpavi/
python -m pipeline.jobs.load_serpavi
python -m pipeline.jobs.export_static
uvicorn apps.api.main:app --reload --port 8000
```

API docs: http://127.0.0.1:8000/docs

### 2. Frontend

```powershell
cd apps/web
npm install
npm run dev
```

Web: http://127.0.0.1:3000

### 3. Export static JSON (for GitHub Pages later)

```powershell
python -m pipeline.jobs.export_static
```

Writes `data/exports/*.json` and copies into `apps/web/public/data/`.

## GitHub public site (recommended path)

**Yes — public repo now, custom domain later.**

| Stage | What we use |
|-------|-------------|
| Now | Local FastAPI + Next.js |
| First public demo | **GitHub Pages** with Next.js `output: 'export'` + prebuilt JSON (no server) |
| Optional easier Next hosting | Free **Vercel** on the same repo (still free; domain later) |
| Later | Buy domain → point to Pages or Vercel |

**Important:** GitHub Pages cannot run FastAPI. Public MVP = static pages fed by exported JSON from the pipeline. Locally you still use the live API.

## Cost principle

No paid cloud, no Idealista scrape, no CAPTCHA bypass. Prefer INE, SERPAVI, AEMET, OurAirports.

## Seed data notice

First metrics are **provisional seeds** (`quality_flag=provisional`) so the product loop works before live ETL. Replace via pipeline jobs; never invent scores without observations.

## License

Private/public repo decision is yours. Data reuse must respect each source’s terms (see `docs/sources.md`).
