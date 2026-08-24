# WhichPlaceGusto — public site

Brand site for the location decision engine MVP.

## Live URL (project Pages under this account)

Because the GitHub user is `mbastugan`, GitHub Pages serves this repository at:

**https://mbastugan.github.io/whichplacegusto.github.io/**

The repository is named `whichplacegusto.github.io` so you can later transfer it to a
GitHub user/organization named `whichplacegusto` and get the apex URL
`https://whichplacegusto.github.io` without renaming the project.

## Local rebuild

From the monorepo root:

```powershell
python -m pipeline.jobs.init_db
python -m pipeline.jobs.load_serpavi
python -m pipeline.jobs.export_static
cd apps/web
$env:NEXT_PUBLIC_DATA_MODE='static'
$env:NEXT_PUBLIC_BASE_PATH='/whichplacegusto.github.io'
npm run build
```

Then publish the `apps/web/out` folder to this repository's `main` branch.
