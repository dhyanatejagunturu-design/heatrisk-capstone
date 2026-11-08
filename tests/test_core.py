import csv

import numpy as np
import pandas as pd
import pytest

from heatrisk.config import load_settings
from heatrisk.datalog import FIELDS, log_download
from heatrisk.exposure.pop_weighted import daily_to_weekly, weighted_mean
from heatrisk.models.baseline import naive_baseline
from heatrisk.vulnerability.landsat import st_dn_to_celsius


def test_settings_cover_five_countries_and_cities():
    s = load_settings()
    assert set(s["countries"]) == {"DE", "FR", "IT", "ES", "EL"}
    assert len(s["cities"]) == 5
    assert s["spatial"]["crs"] == "EPSG:3035"


def test_log_download_writes_header_once(tmp_path):
    log = tmp_path / "log.csv"
    log_download("a.parquet", "Eurostat", "demo_r_mwk3_t", log_path=log)
    log_download("b.zip", "C3S", "eobs", log_path=log)
    rows = list(csv.DictReader(open(log)))
    assert [r["file"] for r in rows] == ["a.parquet", "b.zip"]
    assert list(rows[0]) == FIELDS


def test_weighted_mean_ignores_nan_and_zero_weight():
    assert weighted_mean([10, 20, np.nan], [1, 3, 5]) == pytest.approx(17.5)
    assert np.isnan(weighted_mean([np.nan], [1]))


def test_daily_to_weekly():
    daily = pd.DataFrame(
        {"geo": "DE300", "date": pd.date_range("2024-01-01", periods=7), "temp": range(7)}
    )
    weekly = daily_to_weekly(daily)
    assert weekly.iloc[0].to_dict() == {
        "geo": "DE300", "iso_week": "2024-W01", "temp_mean": 3.0, "temp_max": 6
    }


def test_naive_baseline_uses_only_previous_years():
    df = pd.DataFrame(
        {
            "geo": "DE300",
            "week": 30,
            "year": range(2015, 2022),
            "deaths": [10, 20, 30, 40, 50, 60, 70],
        }
    )
    expected = naive_baseline(df, years=5)
    assert expected.isna().sum() == 5
    assert expected.iloc[5] == 30  # mean of 2015-2019
    assert expected.iloc[6] == 40  # mean of 2016-2020


def test_landsat_conversion():
    out = st_dn_to_celsius(np.array([0, 44000]))
    assert np.isnan(out[0])
    assert out[1] == pytest.approx(44000 * 0.00341802 + 149.0 - 273.15)
