"""Download Eurostat weekly deaths by region, sex and 20-year age group (demo_r_mwk3_20).

Germany reports weekly deaths to Eurostat only at NUTS 1 (federal states), so the
study regions are NUTS 3 for FR, IT, ES, EL and NUTS 1 for DE (see docs/decisions.md).

Run:  python -m heatrisk.data.eurostat_deaths
Output:
  data/raw/demo_r_mwk3_20_<date>.parquet   wide table as delivered
  data/interim/deaths_weekly.parquet       long table: geo, sex, age, iso_week, year, week, deaths
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from heatrisk.config import data_path, load_settings
from heatrisk.datalog import log_download

DATASET = "demo_r_mwk3_20"
URL = f"https://ec.europa.eu/eurostat/databrowser/view/{DATASET}/default/table?lang=en"

# NUTS level used per country: code length 3 = NUTS 1, 5 = NUTS 3
REGION_CODE_LENGTH = {"DE": 3, "FR": 5, "IT": 5, "ES": 5, "EL": 5}


def is_study_region(code: str) -> bool:
    """True for the NUTS level we model in each country.

    Drops 'extra-regio' (..ZZZ) and 'not specified' (..XXX) codes.
    """
    country = code[:2]
    if country not in REGION_CODE_LENGTH or code.endswith(("Z", "X")):
        return False
    return len(code) == REGION_CODE_LENGTH[country]


def study_regions() -> list[str]:
    import eurostat

    return sorted(g for g in eurostat.get_par_values(DATASET, "geo") if is_study_region(g))


def download() -> pd.DataFrame:
    import eurostat

    return eurostat.get_data_df(DATASET, filter_pars={"geo": study_regions()})


def tidy(df: pd.DataFrame, start_year: int = 2010) -> pd.DataFrame:
    """Wide Eurostat table -> long table, one row per geo/sex/age/ISO week."""
    df = df.rename(columns={c: "geo" for c in df.columns if c.lower().startswith("geo")})
    week_cols = [c for c in df.columns if c[:4].isdigit()]
    id_cols = [c for c in ["geo", "sex", "age"] if c in df.columns]
    long = df.melt(id_vars=id_cols, value_vars=week_cols, var_name="iso_week", value_name="deaths")
    long = long.dropna(subset=["deaths"])
    long["year"] = long["iso_week"].str[:4].astype(int)
    long["week"] = long["iso_week"].str[-2:].astype(int)
    long = long[(long["year"] >= start_year) & (long["week"] <= 53)]  # drops 'W99' unknown week
    long["deaths"] = long["deaths"].astype(int)
    return long.sort_values(id_cols + ["iso_week"]).reset_index(drop=True)


def main() -> None:
    today = date.today()
    raw = download()
    raw_out = data_path("raw") / f"{DATASET}_{today:%Y%m%d}.parquet"
    raw_out.parent.mkdir(parents=True, exist_ok=True)
    raw.to_parquet(raw_out, index=False)
    log_download(raw_out.name, "Eurostat", DATASET, version=f"{today:%Y-%m-%d}", url=URL,
                 notes="DE at NUTS 1, others NUTS 3; 2026 weeks provisional")

    countries = list(load_settings()["countries"])
    long = tidy(raw)
    long = long[long["geo"].str[:2].isin(countries)]
    out = data_path("interim") / "deaths_weekly.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    long.to_parquet(out, index=False)
    print(f"{raw_out.name}: {len(raw):,} rows | {out.name}: {len(long):,} rows, "
          f"{long['geo'].nunique()} regions, {long['iso_week'].min()} to {long['iso_week'].max()}")


if __name__ == "__main__":
    main()
