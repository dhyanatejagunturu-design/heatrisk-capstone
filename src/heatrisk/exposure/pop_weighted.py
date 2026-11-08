"""Population-weighted temperature.

Daily E-OBS values are averaged over each region using population as weights,
so the measure reflects heat where people live, not over forests or farmland.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def weighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    """Population-weighted mean that ignores cells with missing temperature."""
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    ok = ~np.isnan(values) & (weights > 0)
    if not ok.any():
        return float("nan")
    return float(np.average(values[ok], weights=weights[ok]))


def daily_to_weekly(daily: pd.DataFrame, value_col: str = "temp") -> pd.DataFrame:
    """Daily region temperatures (geo, date, temp) -> weekly mean and max per ISO week."""
    d = daily.copy()
    d["iso_week"] = pd.to_datetime(d["date"]).dt.strftime("%G-W%V")
    return (
        d.groupby(["geo", "iso_week"])[value_col]
        .agg(temp_mean="mean", temp_max="max")
        .reset_index()
    )
