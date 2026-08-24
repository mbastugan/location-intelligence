"""Rebuild local DB from seed + official loaders, then export static JSON."""

from __future__ import annotations

from pipeline.jobs.export_static import main as export_main
from pipeline.jobs.init_db import main as init_main
from pipeline.jobs.load_ine_urban import main as ine_main
from pipeline.jobs.load_open_meteo_climate import main as climate_main
from pipeline.jobs.load_serpavi import main as serpavi_main


def main() -> None:
    init_main()
    serpavi_main()
    ine_main()
    climate_main()
    export_main()
    print("Full refresh complete")


if __name__ == "__main__":
    main()
