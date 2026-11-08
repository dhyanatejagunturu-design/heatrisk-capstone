"""Link 1 km census cells to study regions.

Each populated cell gets its centre (EPSG:3035 and lon/lat), the study region it falls
in, total population and population aged 65+. This table is the bridge between the
E-OBS temperature grid and the regional deaths, and also gives each region's share of
residents aged 65+.

Run:  python -m heatrisk.exposure.weights
Output:
  data/interim/grid_cells_study.parquet   one row per populated cell
  data/processed/region_population.parquet  geo, name, pop_total, pop_65plus, share_65plus
"""

from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd

from heatrisk.config import data_path
from heatrisk.data.eurostat_deaths import REGION_CODE_LENGTH

GRID_FILE = "census_grid/ESTAT_Census_2021_V3.parquet"
NUTS_FILE = "NUTS_RG_01M_2021_3035_LEVL_{level}.geojson"
SNAP_DISTANCE_M = 2000  # coastal cells whose centre falls just outside a polygon


def study_regions() -> gpd.GeoDataFrame:
    """NUTS 1 polygons for DE and NUTS 3 for the other countries, EPSG:3035.

    French overseas regions (FRY..) are excluded: they are outside the E-OBS domain.
    """
    raw = data_path("raw")
    parts = []
    for level, length in ((1, 3), (3, 5)):
        g = gpd.read_file(raw / NUTS_FILE.format(level=level))
        countries = [c for c, n in REGION_CODE_LENGTH.items() if n == length]
        parts.append(g[g["CNTR_CODE"].isin(countries)])
    regions = pd.concat(parts, ignore_index=True)
    regions = regions[~regions["NUTS_ID"].str.startswith("FRY")]
    regions = regions.rename(columns={"NUTS_ID": "geo", "NAME_LATN": "name"})
    return gpd.GeoDataFrame(regions[["geo", "CNTR_CODE", "name", "geometry"]], crs="EPSG:3035")


def cell_centres(grd_id: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    """GRD_ID 'CRS3035RES1000mN2684000E4285000' gives the lower-left corner; return centres."""
    parts = grd_id.str.extract(r"N(\d+)E(\d+)").astype(float)
    return parts[1].to_numpy() + 500.0, parts[0].to_numpy() + 500.0  # x (east), y (north)


def build_cell_table(regions: gpd.GeoDataFrame) -> pd.DataFrame:
    grid = pd.read_parquet(data_path("raw") / GRID_FILE, columns=["GRD_ID", "T", "Y_GE65",
                                                                   "CNTR_ID"])
    countries = "|".join(sorted(regions["CNTR_CODE"].unique()))
    grid = grid[(grid["T"] > 0) & grid["CNTR_ID"].str.contains(countries)
                & ~grid["GRD_ID"].str.contains("unallocated")]
    x, y = cell_centres(grid["GRD_ID"])
    pts = gpd.GeoDataFrame(grid, geometry=gpd.points_from_xy(x, y), crs="EPSG:3035")

    joined = gpd.sjoin(pts, regions[["geo", "geometry"]], how="left", predicate="within")
    joined = joined[~joined.index.duplicated(keep="first")]
    missing = joined["geo"].isna()
    if missing.any():
        near = gpd.sjoin_nearest(pts[missing], regions[["geo", "geometry"]],
                                 max_distance=SNAP_DISTANCE_M, how="left")
        near = near[~near.index.duplicated(keep="first")]
        joined.loc[missing, "geo"] = near["geo"]
    joined = joined.dropna(subset=["geo"])

    lonlat = joined.geometry.to_crs("EPSG:4326")
    return pd.DataFrame({
        "GRD_ID": joined["GRD_ID"].to_numpy(),
        "geo": joined["geo"].to_numpy(),
        "x": joined.geometry.x.to_numpy(),
        "y": joined.geometry.y.to_numpy(),
        "lon": lonlat.x.to_numpy(),
        "lat": lonlat.y.to_numpy(),
        "pop": joined["T"].to_numpy(),
        # -8888/-9999 = confidential/not available; treat as unknown
        "pop_65plus": joined["Y_GE65"].where(joined["Y_GE65"] >= 0).to_numpy(),
    })


def region_population(cells: pd.DataFrame, regions: gpd.GeoDataFrame) -> pd.DataFrame:
    known = cells.dropna(subset=["pop_65plus"])
    agg = cells.groupby("geo").agg(pop_total=("pop", "sum"), n_cells=("pop", "size"))
    agg["share_65plus"] = (known.groupby("geo")["pop_65plus"].sum()
                           / known.groupby("geo")["pop"].sum())
    out = regions[["geo", "CNTR_CODE", "name"]].merge(agg.reset_index(), on="geo", how="left")
    return out.rename(columns={"CNTR_CODE": "country"})


def main() -> None:
    regions = study_regions()
    cells = build_cell_table(regions)
    out = data_path("interim") / "grid_cells_study.parquet"
    cells.to_parquet(out, index=False)
    pop = region_population(cells, regions)
    pop_out = data_path("processed") / "region_population.parquet"
    pop.to_parquet(pop_out, index=False)
    print(f"{len(cells):,} populated cells in {cells['geo'].nunique()} of {len(regions)} regions")
    print(pop.groupby("country")[["pop_total"]].sum())
    print("regions without cells:", pop.loc[pop["pop_total"].isna(), "geo"].tolist())


if __name__ == "__main__":
    main()
