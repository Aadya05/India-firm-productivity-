"""
productivity_pandas.py
----------------------
Loads and cleans the India firm productivity data (2014, 2022, 2025)
and has one function for each analysis.

Quick start:
    df_clean, report = build_report()

Note: sales_per_employee and value_added_per_employee are in USD
(converted with the exchange rate and adjusted with usd_deflator).
"""
from pathlib import Path

import numpy as np
import pandas as pd

DATA_PATH = Path(__file__).parent / "data" / "India_Productivity_Dataset_Renamed.csv"
GROUP = ["sector", "survey_year"]

# columns that should be numbers
NUMERIC_COLS = [
    "sample_weight", "usd_deflator", "exchange_rate",
    "sales", "employees", "labor_cost", "raw_material_cost", "inventory", "fixed_assets",
    "sales_gdp09", "labor_cost_gdp09", "fixed_assets_gdp09",
    "labor_cost_sales_ratio", "sales_per_employee", "value_added_per_employee",
]

# the survey's own outlier checks
OUTLIER_COLS = [
    "sales_outlier", "labor_cost_outlier", "raw_material_outlier", "fixed_assets_outlier",
    "inventory_outlier", "employees_outlier", "labor_cost_va_outlier", "fixed_assets_va_outlier",
]


# ---------------------------------------------------------------- load and clean
def load_raw(path=DATA_PATH):
    """Read the CSV. low_memory=False stops pandas complaining about mixed types."""
    return pd.read_csv(path, low_memory=False)


def build_clean(raw):
    """Make the data ready for analysis. No rows are dropped."""
    df = raw.copy()

    # some cells contain text like "Don't Know", so turn columns into numbers
    # (text becomes NaN = missing)
    for col in NUMERIC_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["survey_year"] = df["survey_year"].astype(int)

    # a firm is flagged if ANY outlier check says it is an outlier
    df["any_outlier"] = (df[OUTLIER_COLS] != "not an outlier").any(axis=1)

    # logs, used in the regression (log only works for values above 0)
    df["log_sales_per_employee"] = np.log(df["sales_per_employee"].where(df["sales_per_employee"] > 0))
    df["log_employees"] = np.log(df["employees"].where(df["employees"] > 0))
    capital_per_employee = df["fixed_assets_gdp09"] / df["employees"]
    df["log_capital_per_employee"] = np.log(capital_per_employee.where(capital_per_employee > 0))

    # value_added_per_employee is left as it is: it is empty for all Services firms
    return df


# ---------------------------------------------------------------- weighted statistics
def weighted_mean(values, weights):
    """Average that counts each firm by its survey weight."""
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    ok = ~np.isnan(values) & ~np.isnan(weights)
    if not ok.any():
        return np.nan
    return float(np.average(values[ok], weights=weights[ok]))


def weighted_median(values, weights):
    """Middle value when each firm counts by its survey weight."""
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    ok = ~np.isnan(values) & ~np.isnan(weights)
    if not ok.any():
        return np.nan
    values, weights = values[ok], weights[ok]

    order = np.argsort(values)             # sort from smallest to biggest
    values, weights = values[order], weights[order]
    running_total = np.cumsum(weights)     # add up the weights as we go
    half = running_total[-1] / 2           # half of the total weight
    return float(values[np.searchsorted(running_total, half)])


# ---------------------------------------------------------------- ranking
def _add_rank(df, metric, ascending):
    """Rank firms inside each sector-year (like SQL RANK() OVER (PARTITION BY ...))."""
    out = df.dropna(subset=[metric]).copy()
    out["rank_in_group"] = out.groupby(GROUP, observed=True)[metric].rank(method="first", ascending=ascending)
    return out


def top10_productive(df, metric="value_added_per_employee", n=10):
    """Top n firms in each sector-year. Services has no value added, so use
    metric='sales_per_employee' if you want Services included."""
    ranked = _add_rank(df, metric, ascending=False)
    top = ranked[ranked["rank_in_group"] <= n]
    top = top.sort_values(GROUP + ["rank_in_group"])
    return top[GROUP + ["rank_in_group", "firm_id", metric, "employees"]]


def bottom10_productive(df, metric="value_added_per_employee", n=10):
    """Bottom n firms in each sector-year."""
    ranked = _add_rank(df, metric, ascending=True)
    bottom = ranked[ranked["rank_in_group"] <= n]
    bottom = bottom.sort_values(GROUP + ["rank_in_group"])
    return bottom[GROUP + ["rank_in_group", "firm_id", metric, "employees"]]


# ---------------------------------------------------------------- summaries
def avg_labor_cost_ratio(df):
    """Labor cost / sales by sector-year: mean, median and weighted mean."""
    rows = []
    for (sector, year), g in df.groupby(GROUP, observed=True):
        rows.append({
            "sector": sector,
            "survey_year": year,
            "mean": g["labor_cost_sales_ratio"].mean(),
            "median": g["labor_cost_sales_ratio"].median(),
            "weighted_mean": weighted_mean(g["labor_cost_sales_ratio"], g["sample_weight"]),
        })
    return pd.DataFrame(rows)


def productivity_quartiles(df, metric="sales_per_employee"):
    """Split firms into 4 equal groups (Q1 = least productive, Q4 = most productive)
    inside each sector. Like SQL NTILE(4) OVER (PARTITION BY sector)."""
    out = df.dropna(subset=[metric]).copy()
    out["productivity_quartile"] = ""
    for sector in out["sector"].unique():
        rows = out["sector"] == sector
        quartiles = pd.qcut(out.loc[rows, metric], 4, labels=["Q1", "Q2", "Q3", "Q4"])
        out.loc[rows, "productivity_quartile"] = quartiles.astype(str)
    return out


def outlier_rates(df):
    """Share of firms flagged as outliers, by sector-year."""
    rows = []
    for (sector, year), g in df.groupby(GROUP, observed=True):
        rows.append({
            "sector": sector,
            "survey_year": year,
            "firms": len(g),
            "flagged": int(g["any_outlier"].sum()),
            "outlier_rate": g["any_outlier"].mean(),
        })
    return pd.DataFrame(rows)


def sector_year_report(df):
    """Main summary table, one row per sector-year."""
    rows = []
    for (sector, year), g in df.groupby(GROUP, observed=True):
        rows.append({
            "sector": sector,
            "survey_year": year,
            "firms_surveyed": len(g),
            "firms_with_productivity": g["sales_per_employee"].count(),
            "avg_sales_per_employee": g["sales_per_employee"].mean(),
            "median_sales_per_employee": g["sales_per_employee"].median(),
            "wtd_median_sales_per_employee": weighted_median(g["sales_per_employee"], g["sample_weight"]),
            "avg_va_per_employee": g["value_added_per_employee"].mean(),
            "median_va_per_employee": g["value_added_per_employee"].median(),
            "avg_labor_cost_sales": g["labor_cost_sales_ratio"].mean(),
            "median_labor_cost_sales": g["labor_cost_sales_ratio"].median(),
            "avg_employees": g["employees"].mean(),
            "median_employees": g["employees"].median(),
        })
    return pd.DataFrame(rows).round(3)


def build_report(path=DATA_PATH):
    """Load, clean and summarise. Returns (clean data, report table)."""
    df = build_clean(load_raw(path))
    return df, sector_year_report(df)


if __name__ == "__main__":
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)
    df_clean, report = build_report()
    print(f"Clean rows: {len(df_clean):,}\n")
    print(report.to_string(index=False))
