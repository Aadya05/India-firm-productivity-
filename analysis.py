"""
analysis.py
-----------
Runs the whole project:
  1. saves summary tables to outputs/
  2. saves charts to figures/
  3. runs regressions and saves the results

Run it with:  python analysis.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # lets matplotlib save charts without opening a window
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

import productivity_pandas as pp

ROOT = Path(__file__).parent
FIG_DIR = ROOT / "figures"
OUT_DIR = ROOT / "outputs"
FIG_DIR.mkdir(exist_ok=True)
OUT_DIR.mkdir(exist_ok=True)

YEARS = [2014, 2022, 2025]
SECTORS = ["Manufacturing", "Services"]
COLORS = {"Manufacturing": "#1f4e79", "Services": "#e07b39"}


# ---------------------------------------------------------------- 1. tables
def save_tables(df):
    report = pp.sector_year_report(df)
    report.to_csv(OUT_DIR / "sector_year_report.csv", index=False)

    pp.avg_labor_cost_ratio(df).round(4).to_csv(OUT_DIR / "labor_cost_ratio.csv", index=False)
    pp.outlier_rates(df).round(4).to_csv(OUT_DIR / "outlier_rates.csv", index=False)
    pp.top10_productive(df).to_csv(OUT_DIR / "top10_va_per_employee.csv", index=False)
    pp.bottom10_productive(df).to_csv(OUT_DIR / "bottom10_va_per_employee.csv", index=False)
    pp.top10_productive(df, metric="sales_per_employee").to_csv(
        OUT_DIR / "top10_sales_per_employee.csv", index=False)

    # what do the firms in each productivity quartile look like?
    q = pp.productivity_quartiles(df)
    quartile_table = q.groupby(["sector", "productivity_quartile"]).agg(
        firms=("firm_id", "size"),
        median_sales_per_employee=("sales_per_employee", "median"),
        median_employees=("employees", "median"),
        median_labor_cost_sales=("labor_cost_sales_ratio", "median"),
    ).round(3).reset_index()
    quartile_table.to_csv(OUT_DIR / "productivity_quartiles.csv", index=False)
    return report


# ---------------------------------------------------------------- 2. charts
def chart_boxplot(df):
    """Spread of sales per employee for each sector and year (log scale)."""
    fig, ax = plt.subplots(figsize=(9, 5))
    positions, data, colors, labels = [], [], [], []

    place = 0
    for sector in SECTORS:
        for year in YEARS:
            rows = (df["sector"] == sector) & (df["survey_year"] == year)
            values = df.loc[rows, "sales_per_employee"].dropna()
            values = values[values > 0]
            positions.append(place)
            data.append(values)
            colors.append(COLORS[sector])
            labels.append(str(year))
            place += 1
        place += 1  # small gap between the two sectors

    boxes = ax.boxplot(data, positions=positions, widths=0.7, patch_artist=True, showfliers=False)
    for box, color in zip(boxes["boxes"], colors):
        box.set_facecolor(color)
        box.set_alpha(0.75)
    for median_line in boxes["medians"]:
        median_line.set_color("black")

    ax.set_yscale("log")
    ax.set_xticks(positions)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Sales per employee (USD, log scale)")
    ax.set_title("Sales per employee by sector and survey year")
    ax.text(1, -0.14, "Manufacturing", transform=ax.get_xaxis_transform(), ha="center", fontweight="bold")
    ax.text(5, -0.14, "Services", transform=ax.get_xaxis_transform(), ha="center", fontweight="bold")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "01_sales_per_employee_boxplot.png", dpi=150)
    plt.close(fig)


def chart_mean_vs_median(report):
    """Mean, median and weighted median side by side, to show why the mean misleads."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
    x = np.arange(len(YEARS))
    width = 0.27

    for ax, sector in zip(axes, SECTORS):
        r = report[report["sector"] == sector].set_index("survey_year").loc[YEARS]
        ax.bar(x - width, r["avg_sales_per_employee"], width, label="Mean", color="#9aa5b1")
        ax.bar(x, r["median_sales_per_employee"], width, label="Median", color=COLORS[sector])
        ax.bar(x + width, r["wtd_median_sales_per_employee"], width, label="Weighted median", color="#2a2a2a")
        ax.set_xticks(x)
        ax.set_xticklabels(YEARS)
        ax.set_title(sector)
        ax.grid(axis="y", alpha=0.3)

    axes[0].set_ylabel("Sales per employee (USD)")
    axes[0].legend()
    fig.suptitle("Mean vs median sales per employee", fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "02_mean_vs_median.png", dpi=150)
    plt.close(fig)


def chart_labor_cost(df):
    """Median labor cost / sales for each sector and year."""
    table = pp.avg_labor_cost_ratio(df)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(len(YEARS))
    width = 0.38

    for i, sector in enumerate(SECTORS):
        r = table[table["sector"] == sector].set_index("survey_year").loc[YEARS]
        bars = ax.bar(x + (i - 0.5) * width, r["median"], width, label=sector, color=COLORS[sector])
        ax.bar_label(bars, fmt="%.3f", padding=2, fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(YEARS)
    ax.set_ylabel("Median labor cost / sales")
    ax.set_title("Labor cost share of sales (median)")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "03_labor_cost_ratio.png", dpi=150)
    plt.close(fig)


def chart_quartile_size(df):
    """Median number of employees in each productivity quartile."""
    q = pp.productivity_quartiles(df)
    table = q.groupby(["productivity_quartile", "sector"])["employees"].median().unstack()
    ax = table.plot(kind="bar", figsize=(8, 4.5), color=[COLORS[s] for s in table.columns])
    ax.set_ylabel("Median employees")
    ax.set_xlabel("Productivity quartile (Q1 = lowest sales per employee)")
    ax.set_title("Firm size across productivity quartiles")
    ax.grid(axis="y", alpha=0.3)
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "04_quartile_firm_size.png", dpi=150)
    plt.close()


# ---------------------------------------------------------------- 3. regressions
def run_regressions(df):
    """
    Model 1 (all firms):      log(sales per employee) ~ log(employees) + sector x year
    Model 2 (Manufacturing):  log(sales per employee) ~ log(capital per employee) + log(employees) + year
    Each model is run twice: OLS (every firm counts the same)
    and WLS (firms count by survey weight). Robust standard errors (HC1).
    """
    data = df.dropna(subset=["log_sales_per_employee", "log_employees", "sample_weight"]).copy()
    data["year"] = data["survey_year"].astype(str)
    data["sector"] = data["sector"].astype(str)
    formula1 = "log_sales_per_employee ~ log_employees + C(sector) * C(year, Treatment('2014'))"

    mfg = data[data["sector"] == "Manufacturing"].dropna(subset=["log_capital_per_employee"])
    formula2 = ("log_sales_per_employee ~ log_capital_per_employee + log_employees"
                " + C(year, Treatment('2014'))")

    models = {
        "m1_all_ols": smf.ols(formula1, data).fit(cov_type="HC1"),
        "m1_all_wls": smf.wls(formula1, data, weights=data["sample_weight"]).fit(cov_type="HC1"),
        "m2_mfg_ols": smf.ols(formula2, mfg).fit(cov_type="HC1"),
        "m2_mfg_wls": smf.wls(formula2, mfg, weights=mfg["sample_weight"]).fit(cov_type="HC1"),
    }

    # save results as text and as one csv
    text_parts, tables = [], []
    for name, model in models.items():
        text_parts.append(f"===== {name} (n={int(model.nobs):,}, R2={model.rsquared:.3f}) =====")
        text_parts.append(str(model.summary().tables[1]))
        text_parts.append("")

        table = pd.DataFrame({"coef": model.params, "std_err": model.bse, "p_value": model.pvalues})
        table.insert(0, "model", name)
        tables.append(table.reset_index(names="term"))

    (OUT_DIR / "regression_summary.txt").write_text("\n".join(text_parts))
    pd.concat(tables).round(4).to_csv(OUT_DIR / "regression_coefficients.csv", index=False)
    return models


# ---------------------------------------------------------------- run everything
def main():
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)

    df, _ = pp.build_report()
    report = save_tables(df)

    chart_boxplot(df)
    chart_mean_vs_median(report)
    chart_labor_cost(df)
    chart_quartile_size(df)

    models = run_regressions(df)

    print(report.to_string(index=False))
    print()
    for name in ["m1_all_ols", "m2_mfg_ols"]:
        model = models[name]
        print(f"--- {name}: n={int(model.nobs):,}, R2={model.rsquared:.3f}")
        print(pd.DataFrame({"coef": model.params, "p": model.pvalues}).round(4).to_string())
        print()
    print("Saved tables to outputs/ and charts to figures/")


if __name__ == "__main__":
    main()
