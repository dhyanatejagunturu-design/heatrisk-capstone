"""Download E-OBS daily gridded temperature from the Copernicus Climate Data Store.

Needs a CDS account, the E-OBS licence accepted on the dataset page, and ~/.cdsapirc.
Run:  python -m heatrisk.data.eobs
"""

from __future__ import annotations

from heatrisk.config import data_path
from heatrisk.datalog import log_download

DATASET = "insitu-gridded-observations-europe"
URL = "https://cds.climate.copernicus.eu/datasets/insitu-gridded-observations-europe"

REQUEST = {
    "product_type": "ensemble_mean",
    "variable": ["mean_temperature", "maximum_temperature"],
    "grid_resolution": "0_1deg",
    "period": "full_period",
    "version": ["31_0e"],  # check the dataset page for the latest version before downloading
}


def main() -> None:
    import cdsapi

    out = data_path("raw") / "eobs_tg_tx_0.1deg.zip"
    out.parent.mkdir(parents=True, exist_ok=True)
    cdsapi.Client().retrieve(DATASET, REQUEST, str(out))
    log_download(out.name, "Copernicus C3S", DATASET, version=",".join(REQUEST["version"]), url=URL)
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
