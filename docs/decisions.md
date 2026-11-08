# Decisions log

Choices that change the plan in the proposal, or that a reader of the results needs to know.

## 2026-11-08 · Germany modelled at NUTS 1 (federal states)

**Finding.** Eurostat's weekly deaths tables (`demo_r_mwk3_t`, `demo_r_mwk3_20`) contain
Germany only at NUTS 1 (16 states). No NUTS 2 or NUTS 3 weekly deaths are published for
Germany, and Destatis' own weekly series is also by state.

**Decision.** Study regions are NUTS 3 for France, Italy, Spain and Greece (314 regions)
and NUTS 1 for Germany (16 states): 330 regions in total. German thresholds are therefore
state averages and less local than elsewhere; this is stated as a limitation. Berlin is a
state, so the Berlin city analysis is unaffected.

**To confirm with supervisor.**

## 2026-11-08 · Deaths table with age groups

Use `demo_r_mwk3_20` (deaths by week, sex, 20-year age group) instead of
`demo_r_mwk3_t`. It contains the totals as well, and the age groups (especially 80+)
are needed for the LightGBM features and for checking that heat effects concentrate in
older ages.

## 2026-11-08 · Region-code harmonisation

- Sardinia: Eurostat publishes both the old provinces (ITG25–ITG2C, ending 2020-W44) and
  the NUTS 2021 provinces (ITG2D–ITG2H, back-filled from 2015). Keep only NUTS 2021 codes
  to avoid double counting.
- Drop "not specified" (`..XXX`, `DEX`) and "extra-regio" (`..ZZZ`) codes.
- Drop French overseas regions (FRY10–FRY50): outside the E-OBS grid and a different
  climate from the rest of the study.
- All other regions match NUTS 2021 exactly.

## 2026-11-08 · E-OBS from ECA&D, release v34.0e

E-OBS is downloaded from the open ECA&D/KNMI distribution instead of the Copernicus CDS
(same product, no account, newer release available). v34.0e (27 Oct 2026) is the first
release that includes summer 2026. Full-period files are cut to 2010 onwards and the
study bounding box; the full files can be deleted after subsetting.

## 2026-11-08 · Census grid V3

GISCO Census 2021 grid V3 (June 2026) replaces V2.2 linked from the GISCO page. It has
total population and the 65+ age band per 1 km cell. Cells with confidential 65+ values
(-8888) are excluded from the 65+ share only.

## 2026-11-08 · Summer 2026 test data is partial

As of 8 Nov 2026:
- Eurostat weekly deaths end at 2026-W24 for Germany and 2026-W27/W28 elsewhere.
- E-OBS v34.0e ends on 2026-06-30; the next release (expected around April 2027) is too
  late for this project.

Weeks with both deaths and temperature in summer 2026: 4 per country (June), 2 for
Germany. That is too little for a reliable test on its own.

**Proposed.** Following the proposal's risk plan, use **summer 2025 as the main
held-out test** (train 2015–2024) and report June 2026 as an additional out-of-sample
check. To cover July–August 2026, ERA5 / ERA5-Land from the Copernicus CDS (needs an
account; ~5-day delay) could fill the temperature gap, checked against E-OBS on
overlapping dates. Re-download Eurostat deaths before submission to pick up later weeks.

**To confirm with supervisor.**

## 2026-11-08 · Coastal and island populations

About 40 regions had part of their population on 1 km cells that fall on E-OBS sea /
no-data cells (worst: Trieste, Tenerife/La Palma, Dodecanese, Corfu). Those cells are
assigned to the nearest E-OBS cell with data within 25 km. After this, every region has
full population coverage on normal days. E-OBS has one missing day for Greece
(2025-09-12); weeks with 6 of 7 days are kept.

## 2026-11-08 · Small-island weeks without deaths

El Hierro (ES703, 24 weeks) and La Gomera (ES706, 7 weeks) have blank weeks in the
Eurostat table, most likely weeks with zero or very few deaths. They are left missing
rather than filled with zeros; the models use the weeks that exist.
