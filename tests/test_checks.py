import pandas as pd

from heatrisk.checks import (
    duplicated_keys,
    invalid_nuts3_codes,
    missing_iso_weeks,
    out_of_range_temperatures,
)


def test_valid_nuts3_codes_pass():
    codes = pd.Series(["DE300", "FR101", "ITI43", "ES300", "EL303"])
    assert invalid_nuts3_codes(codes, countries=["DE", "FR", "IT", "ES", "EL"]) == []


def test_malformed_and_foreign_codes_flagged():
    codes = pd.Series(["DE3", "de300", "PL911", "DE300"])
    assert invalid_nuts3_codes(codes, countries=["DE"]) == ["DE3", "PL911", "de300"]


def test_missing_iso_weeks_found():
    weeks = pd.Series(["2024-W01", "2024-W02", "2024-W04"])
    assert missing_iso_weeks(weeks) == ["2024-W03"]


def test_week_53_year_boundary():
    # 2020 has 53 ISO weeks
    weeks = pd.Series(["2020-W52", "2020-W53", "2021-W01"])
    assert missing_iso_weeks(weeks) == []
    assert missing_iso_weeks(pd.Series(["2020-W52", "2021-W01"])) == ["2020-W53"]


def test_temperature_range():
    temps = pd.Series([-5.0, 25.0, 300.15, -99.9])
    assert out_of_range_temperatures(temps).tolist() == [300.15, -99.9]


def test_duplicated_keys():
    df = pd.DataFrame({"geo": ["DE300", "DE300", "FR101"], "iso_week": ["2024-W01"] * 3})
    assert len(duplicated_keys(df, ["geo", "iso_week"])) == 2
