"""Lagged quasi-Poisson regression of weekly deaths on temperature (Sprint 2).

Planned model: deaths ~ ns(temp_lag0) + ns(temp_lag1) + ns(temp_lag2)
               + seasonality + trend + region + COVID indicators,
fitted with statsmodels GLM (Poisson family, scale='X2' for overdispersion).
Outputs per region: minimum-mortality temperature, heat threshold, risk curve,
heat-attributable deaths.
"""
