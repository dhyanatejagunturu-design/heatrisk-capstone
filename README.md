# Heat Risk EU

Predicting heat-related mortality and mapping urban heat vulnerability in five
European countries: Germany, France, Italy, Spain and Greece.

MSc Data Science capstone, University of Europe for Applied Sciences, Potsdam.
Authors: Dhyana Teja Gunturu and Sai Vamshi Pakala.

## What it does

The project works at two levels:

- **Regional (NUTS 3).** Weekly Eurostat deaths are linked with
  population-weighted E-OBS temperature. A lagged quasi-Poisson model estimates
  each region's heat threshold and risk curve, and LightGBM plus a naive
  baseline serve as comparisons. Models train on 2015–2025 and test on summer 2026.
- **City (1 km grid).** A Heat Vulnerability Index for Berlin, Paris, Rome,
  Madrid and Athens combines Landsat surface temperature, Sentinel-2 NDVI,
  Urban Atlas land use and the share of residents aged 65+. Local Moran's I
  finds hot-spot clusters.

A Streamlit dashboard shows the maps, risk curves and risk drivers.

## Repository layout

```
config/            settings.yaml: countries, cities, years, CRS, paths
data/              raw/ interim/ processed/ external/ (contents not in git)
data_log.csv       source, version and download date of every data file
docs/              data sources, sprint plan, decisions
notebooks/         exploration notebooks (numbered, e.g. 01_eurostat_deaths.ipynb)
src/heatrisk/
  data/            download + cleaning (Eurostat, E-OBS, GISCO) and panel builder
  exposure/        census cells -> regions, population-weighted temperature
  models/          naive baseline, quasi-Poisson, LightGBM
  vulnerability/   Landsat LST, NDVI, HVI (PCA), hot spots
  validation/      comparison with RKI, Santé publique France, MoMo
  checks.py        data-quality checks used by pipeline and tests
  datalog.py       helper to append to data_log.csv
app/               Streamlit dashboard
tests/             pytest data checks and unit tests
scripts/macos/     one-time macOS setup helpers (Colima signing)
reports/           figures and final report material
```

## Setup

```bash
conda env create -f environment.yml
conda activate heatrisk
pip install -e .
```

On macOS, if you want Docker through Colima, run the one-time steps noted in
`environment.yml`, then `colima start`.

### Data access accounts

| Service | Used for | Setup |
|---|---|---|
| Copernicus Climate Data Store | E-OBS, ERA5-Land | Register, accept the dataset licence, put your key in `~/.cdsapirc` |
| USGS EarthExplorer | Landsat fallback | Register |
| Copernicus Data Space Ecosystem | Sentinel-2 | Register |

Eurostat and GISCO need no account.

## Running

Rebuild the Sprint 1 panel from the public sources, in order:

```bash
python -m heatrisk.data.eurostat_deaths     # weekly deaths by region, sex, age (~4 min)
python -m heatrisk.data.gisco               # NUTS 2021 boundaries + 1 km census grid (~600 MB)
python -m heatrisk.data.eobs --delete-full  # E-OBS tg/tx v34.0e (~9.4 GB download, subset kept)
python -m heatrisk.exposure.weights         # link census cells to regions
python -m heatrisk.exposure.temperature     # population-weighted daily/weekly temperature
python -m heatrisk.data.panel               # panel_weekly.parquet + docs/data_quality_s1.md
```

Other commands:

```bash
pytest                                   # data checks and unit tests
streamlit run app/streamlit_app.py       # dashboard
mlflow ui                                # experiment tracking
```

Study regions: NUTS 3 for FR, IT, ES, EL and NUTS 1 for DE (Eurostat has no finer
weekly deaths for Germany). See `docs/decisions.md`.

## Data notes

2026 mortality figures are provisional. Every downloaded file is recorded in
`data_log.csv` so results can be traced to a data version. Results describe
places, not individuals.

## Licence

Code: MIT (see `LICENSE`). Data remains under its providers' terms.
