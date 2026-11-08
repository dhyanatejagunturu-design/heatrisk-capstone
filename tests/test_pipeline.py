"""Unit tests for the Sprint 1 pipeline steps, using small synthetic inputs."""

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from heatrisk.data.eurostat_deaths import is_study_region, tidy
from heatrisk.data.panel import deaths_wide
from heatrisk.exposure.temperature import (
    daily_to_weekly,
    grid_index,
    regional_daily,
    weight_matrix,
)


def test_study_region_levels():
    assert is_study_region("DE3")          # Germany: NUTS 1
    assert not is_study_region("DE300")
    assert is_study_region("FR101")        # others: NUTS 3
    assert not is_study_region("FR1")
    assert not is_study_region("ESXXX")    # not specified
    assert not is_study_region("ITZZZ")    # extra-regio
    assert not is_study_region("PL911")    # other country


def test_tidy_eurostat_table():
    wide = pd.DataFrame({
        "freq": ["W"], "unit": ["NR"], "sex": ["T"], "age": ["TOTAL"],
        "geo\\TIME_PERIOD": ["FR101"],
        "2015-W01": [100.0], "2015-W02": [np.nan], "2015-W99": [3.0], "2009-W01": [1.0],
    })
    long = tidy(wide)
    assert long[["geo", "iso_week", "year", "week", "deaths"]].to_dict("records") == [
        {"geo": "FR101", "iso_week": "2015-W01", "year": 2015, "week": 1, "deaths": 100}
    ]


def test_grid_index():
    axis = np.array([10.05, 10.15, 10.25])
    assert grid_index(np.array([10.0, 10.11, 10.29, 10.31, 9.99]), axis).tolist() == [
        0, 1, 2, -1, -1
    ]


def test_population_weighting_and_missing_cells():
    # 2x2 E-OBS grid; region A has cells in two E-OBS cells with pop 1 and 3
    lat = np.array([50.05, 50.15])
    lon = np.array([8.05, 8.15])
    cells = pd.DataFrame({
        "geo": ["A", "A", "B"],
        "lat": [50.06, 50.07, 50.14],
        "lon": [8.06, 8.14, 8.14],
        "pop": [1, 3, 5],
    })
    data = np.array([
        [[10.0, 20.0], [0.0, 30.0]],        # day 1: A = (10*1 + 20*3)/4 = 17.5, B = 30
        [[10.0, np.nan], [0.0, 30.0]],      # day 2: A only has the pop-1 cell -> 10
    ])
    da = xr.DataArray(data, dims=("time", "latitude", "longitude"))
    w, regions, li, lj = weight_matrix(cells, lat, lon)
    vals, cov = regional_daily(da, w, li, lj)
    assert regions.tolist() == ["A", "B"]
    assert vals[0].tolist() == pytest.approx([17.5, 30.0])
    assert vals[1].tolist() == pytest.approx([10.0, 30.0])
    assert cov[1].tolist() == pytest.approx([0.25, 1.0])


def test_weekly_drops_partial_weeks():
    dates = pd.date_range("2024-01-01", periods=10)  # Mon 1 Jan .. Wed 10 Jan
    daily = pd.DataFrame({"geo": "A", "date": dates, "tg": range(10),
                          "tx": np.arange(10) + 5.0, "coverage": 1.0})
    weekly = daily_to_weekly(daily)
    assert weekly["iso_week"].tolist() == ["2024-W01"]
    row = weekly.iloc[0]
    assert (row["tg_mean"], row["tx_max"], row["n_days"]) == (3.0, 11.0, 7)


def test_deaths_wide():
    deaths = pd.DataFrame({
        "geo": "A", "sex": ["T", "T", "M"], "age": ["TOTAL", "Y_GE80", "TOTAL"],
        "iso_week": "2024-W01", "year": 2024, "week": 1, "deaths": [10, 6, 5],
    })
    out = deaths_wide(deaths)
    assert out.loc[0, "deaths"] == 10
    assert out.loc[0, "deaths_80plus"] == 6


def test_coastal_cells_snap_to_nearest_valid_cell():
    lat = np.array([50.05, 50.15])
    lon = np.array([8.05, 8.15])
    valid = np.array([[True, False], [False, False]])   # only the south-west cell has data
    cells = pd.DataFrame({"geo": ["A", "A"], "lat": [50.06, 50.06], "lon": [8.06, 8.14],
                          "pop": [1, 3]})
    w, _, li, lj = weight_matrix(cells, lat, lon, valid)
    assert (li.tolist(), lj.tolist()) == ([0], [0])     # both cells now use the valid cell
    assert w.toarray().tolist() == [[4.0]]
