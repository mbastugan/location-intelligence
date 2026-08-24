# GitHub Pages + static site notes

## Recommended approach

1. Keep developing locally with FastAPI + Next.js (`NEXT_PUBLIC_DATA_MODE=api`).
2. When ready for a public demo:
   - `python -m pipeline.jobs.export_static`
   - Build with `NEXT_PUBLIC_DATA_MODE=static` (`npm run export:static` in `apps/web`)
   - Publish `apps/web/out` to GitHub Pages (project site or user site).

3. Buy a custom domain later and point DNS to GitHub Pages (or Vercel).

## Why not FastAPI on GitHub Pages?

GitHub Pages only serves static files. The API stays local (and later can move to a free/cheap host if needed). Static JSON export is enough for the 3-city MVP.

## Optional: Vercel

Connecting the same GitHub repo to Vercel free tier is often easier for Next.js. Still free; domain later. Pages remains fine if we stay on static export.

## Enabling GitHub Actions deploy

The workflow file lives at `docs/pages.workflow.yml.example` because the initial GitHub OAuth token lacked the `workflow` scope.

To enable automatic Pages deploys:

1. Re-auth `gh` with `workflow` scope, **or** add the file in the GitHub UI.
2. Copy to `.github/workflows/pages.yml` and push.
3. Repo → Settings → Pages → Source: **GitHub Actions**.
