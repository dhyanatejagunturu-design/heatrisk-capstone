"""Build the Sprint 1 deliverable: weekly deaths-and-temperature panel per study region.

Run:  python -m heatrisk.data.panel
Output:
  data/processed/panel_weekly.parquet
  docs/data_quality_s1.md   (generated check report)
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from heatrisk.checks import (
    duplicated_keys,
    invalid_nuts3_codes,
    missing_iso_weeks,
    out_of_range_temperatures,
)
from heatrisk.config import PROJECT_ROOT, data_path, load_settings
from heatrisk.data.eobs import VERSION

AGE_GROUPS = {"Y_LT20": "deaths_lt20", "Y20-39": "deaths_20_39", "Y40-59": "deaths_40_59",
              "Y60-79": "deaths_60_79", "Y_GE80": "deaths_80plus"}


def deaths_wide(deaths: pd.DataFrame) -> pd.DataFrame:
    """Total deaths plus deaths by age group, both sexes, one row per geo/week."""
    both = deaths[deaths["sex"] == "T"]
    total = both[both["age"] == "TOTAL"][["geo", "iso_week", "year", "week", "deaths"]]
    ages = (both[both["age"].isin(AGE_GROUPS)]
            .pivot_table(index=["geo", "iso_week"], columns="age", values="deaths")
            .rename(columns=AGE_GROUPS).reset_index())
    return total.merge(ages, on=["geo", "iso_week"], how="left")


def build_panel() -> pd.DataFrame:
    s = load_settings()
    deaths = pd.read_parquet(data_path("interim") / "deaths_weekly.parquet")
    temp = pd.read_parquet(data_path("processed") / "temperature_weekly.parquet")
    pop = pd.read_parquet(data_path("processed") / "region_population.parquet")

    panel = deaths_wide(deaths).merge(pop[["geo", "country", "name", "pop_total",
                                           "share_65plus"]], on="geo", how="inner")
    panel = panel.merge(temp, on=["geo", "iso_week"], how="left")
    panel = panel[panel["year"] >= s["period"]["train_start"] - 5]

    p = s["period"]
    week_start = pd.to_datetime(panel["iso_week"] + "-1", format="%G-W%V-%u")
    panel["week_start"] = week_start
    panel["summer"] = week_start.dt.month.isin(p["summer_months"])
    panel["covid"] = panel["year"].isin(p["covid_years"])
    panel["split"] = "history"
    panel.loc[panel["year"].between(p["train_start"], p["train_end"]), "split"] = "train"
    panel.loc[panel["year"] == p["test_year"], "split"] = "test"
    panel["deaths_per_100k"] = panel["deaths"] / panel["pop_total"] * 1e5
    return panel.sort_values(["geo", "iso_week"]).reset_index(drop=True)


def quality_report(panel: pd.DataFrame) -> str:
    countries = list(load_settings()["countries"])
    lines = [f"# Sprint 1 data-quality report\n\nGenerated {date.today():%Y-%m-%d} by "
             "`python -m heatrisk.data.panel`.\n"]
    lines.append(f"- Rows: {len(panel):,}; regions: {panel['geo'].nunique()}; weeks "
                 f"{panel['iso_week'].min()} to {panel['iso_week'].max()}")
    lines.append(f"- Duplicate geo/week rows: {len(duplicated_keys(panel, ['geo', 'iso_week']))}")
    codes = panel["geo"]
    bad = invalid_nuts3_codes(codes[codes.str.len() == 5], countries)
    lines.append(f"- Malformed NUTS 3 codes: {bad or 'none'}")
    no_temp = panel[panel["tg_mean"].isna()]
    lines.append(f"- Weeks without temperature: {len(no_temp):,} "
                 f"(weeks from {no_temp['iso_week'].min()}; E-OBS {VERSION} ends 2026-06-30)"
                 if len(no_temp) else "- Weeks without temperature: 0")
    oor = out_of_range_temperatures(pd.concat([panel['tg_mean'], panel['tx_max']]).dropna())
    lines.append(f"- Temperatures outside -40..50 C: {len(oor)}")
    lines.append(f"- Lowest weekly population coverage of temperature: "
                 f"{panel['coverage'].min():.1%}\n")

    lines.append("## Coverage by country\n")
    lines.append("| Country | Regions | First week | Last week | Missing weeks | Last 2026 week |")
    lines.append("|---|---|---|---|---|---|")
    for c, g in panel.groupby("country"):
        gaps = sum(len(missing_iso_weeks(x["iso_week"])) for _, x in g.groupby("geo"))
        last26 = g.loc[g["year"] == 2026, "iso_week"].max()
        lines.append(f"| {c} | {g['geo'].nunique()} | {g['iso_week'].min()} | "
                     f"{g['iso_week'].max()} | {gaps} | {last26} |")

    lines.append("\n## Summer weeks with both deaths and temperature (June-August)\n")
    lines.append("| Country | 2025 summer weeks | 2026 summer weeks |")
    lines.append("|---|---|---|")
    summer = panel[panel["summer"] & panel["tg_mean"].notna()]
    for c, g in summer.groupby("country"):
        n25 = g.loc[g["year"] == 2025, "iso_week"].nunique()
        n26 = g.loc[g["year"] == 2026, "iso_week"].nunique()
        lines.append(f"| {c} | {n25} | {n26} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    panel = build_panel()
    out = data_path("processed") / "panel_weekly.parquet"
    panel.to_parquet(out, index=False)
    report = quality_report(panel)
    (PROJECT_ROOT / "docs" / "data_quality_s1.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
