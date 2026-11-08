"""Population-weighted daily and weekly temperature per study region.

Each populated 1 km census cell is matched to the E-OBS 0.1 degree cell it lies in.
Cells that fall on an E-OBS cell that never has data (sea, some coast and small islands)
are moved to the nearest E-OBS cell with data within 25 km. A sparse
region-by-E-OBS-cell weight matrix (population counts) then turns each day's
temperature grid into regional values in one matrix product. E-OBS cells with no value
on a given day are left out and the remaining weights renormalised; the share of
population covered is kept as `coverage`.

Run:  python -m heatrisk.exposure.temperature
Output:
  data/interim/temperature_daily.parquet   geo, date, tg, tx, coverage
  data/processed/temperature_weekly.parquet  geo, iso_week, tg_mean, tx_mean, tx_max, n_days,
                                             coverage
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import xarray as xr
from scipy import sparse

from heatrisk.config import data_path
from heatrisk.data.eobs import VERSION

VARIABLES = ("tg", "tx")
SNAP_MAX_KM = 25.0  # coastal/island cells: use nearest E-OBS cell with data within this
MIN_DAYS_PER_WEEK = 6


def grid_index(values: np.ndarray, axis: np.ndarray) -> np.ndarray:
    """Index of the regular-grid cell containing each value (-1 if outside)."""
    step = float(axis[1] - axis[0])
    idx = np.floor((values - (axis[0] - step / 2)) / step).astype(int)
    idx[(idx < 0) | (idx >= len(axis))] = -1
    return idx


def valid_mask(da: xr.DataArray, sample_every: int = 30, min_share: float = 0.5) -> np.ndarray:
    """E-OBS cells that usually have data (the land mask), from a sample of days."""
    sample = da.isel(time=slice(0, None, sample_every)).notnull().mean("time")
    return sample.to_numpy() >= min_share


def snap_to_valid(i: np.ndarray, j: np.ndarray, lat: np.ndarray, lon: np.ndarray,
                  valid: np.ndarray, max_km: float = SNAP_MAX_KM) -> tuple[np.ndarray, np.ndarray]:
    """Move cells that land on a no-data E-OBS cell (sea, coast) to the nearest valid one."""
    from scipy.spatial import cKDTree

    i, j = i.copy(), j.copy()
    inside = (i >= 0) & (j >= 0)
    bad = inside.copy()
    bad[inside] = ~valid[i[inside], j[inside]]
    if not bad.any():
        return i, j
    vi, vj = np.nonzero(valid)

    def xy(ii, jj):  # approximate km on a local plane
        la = lat[ii]
        return np.column_stack([la * 111.0, lon[jj] * 111.0 * np.cos(np.radians(la))])

    dist, k = cKDTree(xy(vi, vj)).query(xy(i[bad], j[bad]), distance_upper_bound=max_km)
    found = np.isfinite(dist)
    bi = np.flatnonzero(bad)
    i[bi[found]], j[bi[found]] = vi[k[found]], vj[k[found]]
    i[bi[~found]], j[bi[~found]] = -1, -1
    return i, j


def weight_matrix(cells: pd.DataFrame, lat: np.ndarray, lon: np.ndarray,
                  valid: np.ndarray | None = None):
    """Sparse (regions x used E-OBS cells) population matrix plus lookup arrays.

    If `valid` (E-OBS land mask) is given, cells on no-data E-OBS cells are snapped to
    the nearest valid cell within SNAP_MAX_KM.
    """
    i = grid_index(cells["lat"].to_numpy(), lat)
    j = grid_index(cells["lon"].to_numpy(), lon)
    if valid is not None:
        i, j = snap_to_valid(i, j, lat, lon, valid)
    ok = (i >= 0) & (j >= 0)
    cells = cells[ok]
    flat = i[ok] * len(lon) + j[ok]
    used, col = np.unique(flat, return_inverse=True)
    regions, row = np.unique(cells["geo"].to_numpy(), return_inverse=True)
    w = sparse.csr_matrix((cells["pop"].to_numpy(dtype=float), (row, col)),
                          shape=(len(regions), len(used)))
    return w, regions, used // len(lon), used % len(lon)


def regional_daily(da: xr.DataArray, w, lat_i, lon_j, chunk_days: int = 366):
    """(days x regions) population-weighted values and coverage, processed in chunks."""
    total = np.asarray(w.sum(axis=1)).ravel()
    values, coverage = [], []
    for start in range(0, da.sizes["time"], chunk_days):
        block = da.isel(time=slice(start, start + chunk_days)).to_numpy()
        arr = block[:, lat_i, lon_j]                     # days x used cells
        valid = ~np.isnan(arr)
        num = w @ np.where(valid, arr, 0.0).T             # regions x days
        den = w @ valid.T.astype(float)
        with np.errstate(invalid="ignore", divide="ignore"):
            values.append((num / den).T)
        coverage.append((den / total[:, None]).T)
    return np.vstack(values), np.vstack(coverage)


def daily_to_weekly(daily: pd.DataFrame) -> pd.DataFrame:
    d = daily.copy()
    d["iso_week"] = d["date"].dt.strftime("%G-W%V")
    weekly = d.groupby(["geo", "iso_week"]).agg(
        tg_mean=("tg", "mean"), tx_mean=("tx", "mean"), tx_max=("tx", "max"),
        n_days=("tg", "count"), coverage=("coverage", "mean"),
    ).reset_index()
    # drop partial weeks at the series edges; allow one missing day (e.g. EL 2025-09-12)
    return weekly[weekly["n_days"] >= MIN_DAYS_PER_WEEK]


def main() -> None:
    cells = pd.read_parquet(data_path("interim") / "grid_cells_study.parquet")
    frames = {}
    for var in VARIABLES:
        ds = xr.open_dataset(data_path("interim") / f"eobs_{var}_{VERSION}_study.nc")
        w, regions, lat_i, lon_j = weight_matrix(cells, ds["latitude"].values,
                                                 ds["longitude"].values, valid_mask(ds[var]))
        vals, cov = regional_daily(ds[var], w, lat_i, lon_j)
        times = pd.to_datetime(ds["time"].values)
        frames[var] = pd.DataFrame(vals, index=times, columns=regions)
        if var == "tg":
            frames["coverage"] = pd.DataFrame(cov, index=times, columns=regions)
        ds.close()

    long = {k: v.stack().rename(k) for k, v in frames.items()}
    daily = pd.concat(long, axis=1).rename_axis(["date", "geo"]).reset_index()
    daily = daily[["geo", "date", "tg", "tx", "coverage"]].sort_values(["geo", "date"])
    daily.to_parquet(data_path("interim") / "temperature_daily.parquet", index=False)

    weekly = daily_to_weekly(daily)
    weekly.to_parquet(data_path("processed") / "temperature_weekly.parquet", index=False)
    print(f"daily: {len(daily):,} rows, {daily['date'].min():%Y-%m-%d} to "
          f"{daily['date'].max():%Y-%m-%d} | weekly: {len(weekly):,} rows, "
          f"{weekly['geo'].nunique()} regions")


if __name__ == "__main__":
    main()
