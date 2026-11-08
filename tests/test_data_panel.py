"""Data checks on the real Sprint 1 panel.

Skipped when data/processed/panel_weekly.parquet is absent (e.g. on GitHub Actions,
where raw data is not available). Run locally after `python -m heatrisk.data.panel`.
"""

import pandas as pd
import pytest

from heatrisk.checks import duplicated_keys, invalid_nuts3_codes, out_of_range_temperatures
from heatrisk.config import data_path, load_settings

PANEL = data_path("processed") / "panel_weekly.parquet"

pytestmark = pytest.mark.skipif(not PANEL.exists(), reason="panel not built locally")


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    return pd.read_parquet(PANEL)


def test_one_row_per_region_week(panel):
    assert duplicated_keys(panel, ["geo", "iso_week"]).empty


def test_region_set(panel):
    countries = list(load_settings()["countries"])
    assert panel["geo"].nunique() == 330
    assert set(panel["country"]) == set(countries)
    de = panel.loc[panel["country"] == "DE", "geo"]
    assert de.str.len().eq(3).all()              # Germany at NUTS 1
    other = panel.loc[panel["country"] != "DE", "geo"]
    assert invalid_nuts3_codes(other, countries) == []


def test_training_years_complete(panel):
    train = panel[panel["split"] == "train"]
    assert train["year"].min() == 2015 and train["year"].max() == 2025
    assert train["tg_mean"].notna().all()        # temperature for every training week


def test_plausible_values(panel):
    assert out_of_range_temperatures(panel["tg_mean"].dropna()).empty
    assert out_of_range_temperatures(panel["tx_max"].dropna()).empty
    t = panel.dropna(subset=["tg_mean", "tx_max"])
    assert (t["tx_max"] >= t["tg_mean"]).all()
    assert (panel["deaths"] >= 0).all()
    assert panel["coverage"].dropna().min() > 0.8


def test_population_and_age_share(panel):
    pop = panel.groupby("geo")["pop_total"].first()
    assert (pop > 0).all()
    share = panel.groupby("geo")["share_65plus"].first()
    assert share.between(0.05, 0.45).all()
