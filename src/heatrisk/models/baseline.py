"""Naive baseline: mean deaths in the same ISO week over the previous N years."""

from __future__ import annotations

import pandas as pd


def naive_baseline(df: pd.DataFrame, years: int = 5) -> pd.Series:
    """Expected deaths for each row of a (geo, year, week, deaths) table.

    Uses only earlier years, so it is a fair forecast for the test period.
    Rows without `years` earlier observations get NaN.
    """
    d = df.sort_values(["geo", "week", "year"])
    expected = (
        d.groupby(["geo", "week"])["deaths"]
        .transform(lambda s: s.shift(1).rolling(years, min_periods=years).mean())
    )
    return expected.reindex(df.index)
