# Data sources

All links checked live in October 2026. Re-check access terms at the start of Sprint 1.
Every downloaded file goes in `data_log.csv` (source, version, download date).

## Core (pan-European)

| Dataset | Provider | Use | Link |
|---|---|---|---|
| Deaths by week, sex, NUTS 3 (`demo_r_mwk3_t`) | Eurostat | Weekly mortality 2015–2026 | https://ec.europa.eu/eurostat/databrowser/view/demo_r_mwk3_t/default/table?lang=en |
| E-OBS daily gridded observations (v34.0e, to 2026-06-30) | Copernicus C3S / ECA&D | Daily mean and max temperature, 0.1° | https://cds.climate.copernicus.eu/datasets/insitu-gridded-observations-europe (files used: https://knmi-ecad-assets-prd.s3.amazonaws.com/ensembles/data/Grid_0.1deg_reg_ensemble/) |
| ERA5-Land hourly (optional) | Copernicus C3S | Humidity for apparent temperature | https://doi.org/10.24381/cds.e2161bac |
| Census 2021 population grid, 1 km (V3) | Eurostat GISCO | Population weights, share aged 65+ | https://gisco-services.ec.europa.eu/census/2021/Eurostat_Census-GRID_2021_V3.zip |
| Deaths by week, sex, 20-year age group (`demo_r_mwk3_20`) | Eurostat | Age-specific weekly deaths (used instead of `demo_r_mwk3_t`) | https://ec.europa.eu/eurostat/databrowser/view/demo_r_mwk3_20/default/table?lang=en |
| Landsat 8/9 C2 L2 surface temperature | USGS | Summer LST at 30 m | https://www.usgs.gov/land-resources/nli/landsat/landsat-collection-2-level-2-science-products |
| Sentinel-2 L2A | ESA / Copernicus Data Space | NDVI | https://dataspace.copernicus.eu |
| Urban Atlas 2021 | Copernicus Land Monitoring Service | Land use, street trees, building height | https://land.copernicus.eu/en/news/urban-atlas-2021-product-update-is-now-available |
| NUTS boundaries | Eurostat GISCO | Region shapes | https://ec.europa.eu/eurostat/web/gisco/geodata/statistical-units/territorial-units-statistics |

## Validation (national)

| Dataset | Provider | Link |
|---|---|---|
| Heat mortality reports | Robert Koch Institute (DE) | https://www.rki.de |
| Heat and health data | Santé publique France (FR) | https://www.santepubliquefrance.fr/fortes-chaleurs-canicule/donnees |
| MoMo mortality monitoring | ISCIII (ES) | https://www.sanidad.gob.es/va/areas/sanidadAmbiental/riesgosAmbientales/frioExtremo/momoBajasTemperaturas.htm |
| Daily deaths by municipality | ISTAT (IT) | https://www.istat.it/it/archivio/240401 |
| Station data | DWD | https://opendata.dwd.de/climate_environment/CDC/ |
| Station data | Météo-France | https://meteo.data.gouv.fr |
| Station data | AEMET | https://opendata.aemet.es/centrodedescargas/productosAEMET |
| Station data | NOA / CLIMPACT | https://data.climpact.gr/en/dataset/497dc26d-45e0-4ad5-b8f3-5f8890f65129 |
| Climate Analysis 2022 | Berlin Environmental Atlas | https://www.berlin.de/umweltatlas/klima/klimaanalyse/2022/download/ |

## Processing conventions

- CRS: ETRS89-LAEA (EPSG:3035) for all spatial data.
- Time: ISO weeks (`2024-W07`).
- Regions: NUTS version used by the Eurostat deaths table (see `config/settings.yaml`).
- Landsat ST: Kelvin = DN × 0.00341802 + 149.0 (see `heatrisk.vulnerability.landsat`).
