"""Download GISCO geodata: NUTS 2021 boundaries and the Census 2021 1 km population grid.

Run:  python -m heatrisk.data.gisco
"""

from __future__ import annotations

import urllib.request
import zipfile
from pathlib import Path

from heatrisk.config import data_path
from heatrisk.datalog import log_download

NUTS_URL = (
    "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/"
    "NUTS_RG_01M_2021_3035_LEVL_{level}.geojson"
)
GRID_VERSION = "V3"
GRID_URL = f"https://gisco-services.ec.europa.eu/census/2021/Eurostat_Census-GRID_2021_{GRID_VERSION}.zip"


def fetch(url: str, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        print(f"exists, skipping: {out.name}")
        return out
    tmp = out.with_suffix(out.suffix + ".part")
    print(f"downloading {url}")
    urllib.request.urlretrieve(url, tmp)
    tmp.rename(out)
    return out


def main() -> None:
    raw = data_path("raw")
    for level in (1, 3):
        url = NUTS_URL.format(level=level)
        out = fetch(url, raw / Path(url).name)
        log_download(out.name, "Eurostat GISCO", f"NUTS_2021_LEVL_{level}", version="2021, 1:1M",
                     url=url)
    out = fetch(GRID_URL, raw / Path(GRID_URL).name)
    log_download(out.name, "Eurostat GISCO", "Census-GRID_2021", version=GRID_VERSION, url=GRID_URL,
                 notes="1 km grid, total population and age groups")
    extract_grid(out, raw / "census_grid")


def extract_grid(archive: Path, dest: Path) -> None:
    """Extract only the parquet table and read.me from the census grid archive."""
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        for member in z.namelist():
            name = Path(member).name
            if name.endswith("_V3.parquet") or name == "read.me":
                (dest / name).write_bytes(z.read(member))


if __name__ == "__main__":
    main()
