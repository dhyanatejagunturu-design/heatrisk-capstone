"""E-OBS daily gridded temperature (0.1 degree), from the open ECA&D/KNMI distribution.

The same product is on the Copernicus Climate Data Store, but the ECA&D copy needs
no account and gets new releases first. Release v34.0e (Oct 2026) includes summer 2026.

Run:  python -m heatrisk.data.eobs
Steps:
  1. download full-period files for tg (daily mean) and tx (daily max) to data/raw/eobs/
  2. subset to the study area and years -> data/interim/eobs_{tg,tx}_<version>_study.nc
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import xarray as xr

from heatrisk.config import data_path, load_settings
from heatrisk.datalog import log_download

VERSION = "v34.0e"
BASE_URL = "https://knmi-ecad-assets-prd.s3.amazonaws.com/ensembles/data/Grid_0.1deg_reg_ensemble"
VARIABLES = {"tg": "daily mean temperature", "tx": "daily maximum temperature"}

# Bounding box covering DE, FR, IT, ES, EL including the Canary Islands, Ceuta/Melilla
# and the eastern Greek islands (lon/lat, degrees). French overseas regions (FRY) are
# outside the E-OBS domain and excluded from the study.
BBOX = {"lon_min": -18.5, "lon_max": 30.0, "lat_min": 27.5, "lat_max": 55.5}


def file_name(var: str) -> str:
    return f"{var}_ens_mean_0.1deg_reg_{VERSION}.nc"


def download(var: str) -> Path:
    out = data_path("raw") / "eobs" / file_name(var)
    out.parent.mkdir(parents=True, exist_ok=True)
    url = f"{BASE_URL}/{file_name(var)}"
    # curl resumes partial downloads (-C -); files are ~4.7 GB each
    subprocess.run(["curl", "-sS", "-fL", "-C", "-", "-o", str(out), url], check=True)
    log_download(out.name, "ECA&D / Copernicus C3S", f"E-OBS {var}", version=VERSION, url=url,
                 notes=VARIABLES[var] + "; full period, subset kept in data/interim")
    return out


def subset(src: Path, var: str, start_year: int) -> Path:
    out = data_path("interim") / f"eobs_{var}_{VERSION}_study.nc"
    out.parent.mkdir(parents=True, exist_ok=True)
    with xr.open_dataset(src) as ds:
        sub = ds[[var]].sel(
            time=slice(f"{start_year}-01-01", None),
            longitude=slice(BBOX["lon_min"], BBOX["lon_max"]),
            latitude=slice(BBOX["lat_min"], BBOX["lat_max"]),
        )
        sub = sub.astype("float32")
        sub.to_netcdf(out, encoding={var: {"zlib": True, "complevel": 4}})
    return out


def main(delete_full: bool = False) -> None:
    start_year = load_settings()["period"]["train_start"] - 5  # room for the 5-year baseline
    for var in VARIABLES:
        src = download(var)
        out = subset(src, var, start_year)
        print(f"{var}: {out}")
        if delete_full:
            src.unlink()


if __name__ == "__main__":
    import sys

    main(delete_full="--delete-full" in sys.argv)
