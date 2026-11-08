"""Download Eurostat weekly deaths by NUTS 3 region (demo_r_mwk3_t).

Run:  python -m heatrisk.data.eurostat_deaths
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from heatrisk.config import data_path, load_settings
from heatrisk.datalog import log_download

DATASET = "demo_r_mwk3_t"
URL = f"https://ec.europa.eu/eurostat/databrowser/view/{DATASET}/default/table?lang=en"


def download() -> pd.DataFrame:
    import eurostat  # imported here so tests don't need the package

    countries = list(load_settings()["countries"])
    df = eurostat.get_data_df(DATASET)
    geo_col = next(c for c in df.columns if c.lower().startswith("geo"))
    df = df[df[geo_col].str[:2].isin(countries) & (df[geo_col].str.len() == 5)]
    return df


def tidy(df: pd.DataFrame) -> pd.DataFrame:
    """Wide Eurostat table -> long table: geo, sex, iso_week, deaths."""
    geo_col = next(c for c in df.columns if c.lower().startswith("geo"))
    id_cols = [c for c in df.columns if not c[:4].isdigit()]
    long = df.melt(id_vars=id_cols, var_name="iso_week", value_name="deaths")
    long = long.rename(columns={geo_col: "geo"})
    long["iso_week"] = long["iso_week"].str.replace("W", "-W", regex=False)
    return long.dropna(subset=["deaths"])


def main() -> None:
    raw = download()
    out = data_path("raw") / f"{DATASET}_{date.today():%Y%m%d}.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    raw.to_parquet(out, index=False)
    log_download(out.name, "Eurostat", DATASET, version=f"{date.today():%Y-%m-%d}", url=URL,
                 notes="2026 weeks provisional")
    print(f"Saved {len(raw):,} rows to {out}")


if __name__ == "__main__":
    main()
