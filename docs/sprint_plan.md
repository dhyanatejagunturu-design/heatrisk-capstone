# Sprint plan

| Sprint | Checkpoint | Focus | Deliverable |
|---|---|---|---|
| S1 | 10 Nov 2026 | Data access and pipeline foundation | Clean weekly deaths-and-temperature panel, all NUTS 3, 2015–2026 |
| S2 | 24 Nov 2026 | Regional mortality model | Heat threshold and risk curve per region, first model comparison |
| S3 | 8 Dec 2026 | City vulnerability and validation | Five city HVI maps and a validation report |
| S4 | 22 Dec 2026 | Dashboard and handover | Documented dashboard and final report |

## S1 checklist

- [x] Repository, environment, CI
- [ ] Accounts: Copernicus CDS, USGS EarthExplorer, Copernicus Data Space
- [ ] Download Eurostat deaths, NUTS boundaries, E-OBS, 1 km census grid
- [ ] Document schemas, missing weeks, region-code changes; start data log
- [ ] Population-weighted weekly temperature per NUTS 3 region
- [ ] First pytest data checks on real data

## S2 checklist

- [ ] Expected-deaths baseline with seasonality and trend
- [ ] Lagged quasi-Poisson model; thresholds and risk curves
- [ ] LightGBM and naive baseline
- [ ] COVID-19 indicators and sensitivity check
- [ ] All runs in MLflow

## S3 checklist

- [ ] Median summer LST (Landsat, 2022–2026) for five cities
- [ ] Sentinel-2 NDVI, Urban Atlas trees and building height, share 65+
- [ ] HVI (PCA weights) and Local Moran's I hot spots
- [ ] Validate vs RKI, Santé publique France, MoMo; SHAP
- [ ] Berlin HVI vs Environmental Atlas

## S4 checklist

- [ ] Streamlit dashboard: maps, risk curves, drivers, country comparison
- [ ] Complete tests and CI
- [ ] Deploy to Streamlit Community Cloud if feasible
- [ ] Limitations, data versions, final configuration
- [ ] Report, presentation, demo
