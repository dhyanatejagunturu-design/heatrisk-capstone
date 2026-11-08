"""Data-quality checks shared by the pipeline and the pytest suite."""

from __future__ import annotations

import re

import pandas as pd

# NUTS 3 code: 2-letter country + 3 alphanumeric characters, e.g. DE300, FR101, EL303
NUTS3_PATTERN = re.compile(r"^[A-Z]{2}[0-9A-Z]{3}$")

# Plausible daily air temperature in the study area (degrees C)
TEMP_MIN_C = -40.0
TEMP_MAX_C = 50.0


def invalid_nuts3_codes(codes: pd.Series, countries: list[str] | None = None) -> list[str]:
    """Return codes that are not well-formed NUTS 3 codes (or not in `countries`)."""
    bad = []
    for code in codes.dropna().astype(str).unique():
        if not NUTS3_PATTERN.match(code):
            bad.append(code)
        elif countries is not None and code[:2] not in countries:
            bad.append(code)
    return sorted(bad)


def missing_iso_weeks(weeks: pd.Series) -> list[str]:
    """Return ISO weeks ('2024-W07') missing between the first and last week present.

    Accepts strings like '2024-W07' (Eurostat uses this form) and handles 53-week years.
    """
    present = set(weeks.dropna().astype(str))
    if not present:
        return []
    mondays = sorted(pd.to_datetime([w + "-1" for w in present], format="%G-W%V-%u"))
    full = pd.date_range(mondays[0], mondays[-1], freq="W-MON")
    expected = {d.strftime("%G-W%V") for d in full}
    return sorted(expected - present)


def out_of_range_temperatures(
    temps: pd.Series, low: float = TEMP_MIN_C, high: float = TEMP_MAX_C
) -> pd.Series:
    """Return values outside the plausible range (likely unit or fill-value errors)."""
    return temps[(temps < low) | (temps > high)]


def duplicated_keys(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Return rows whose key columns appear more than once."""
    return df[df.duplicated(subset=keys, keep=False)]
