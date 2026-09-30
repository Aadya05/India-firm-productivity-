# India Firm Productivity: Pandas Analysis Project

A Python/pandas project analysing firm-level productivity in India using World Bank Enterprise Survey style data: **29,136 firms**, three survey years (**2014, 2022, 2025**) and two sectors (**Manufacturing, Services**).

## What this project demonstrates
- Loading and type-cleaning a messy real-world CSV (text like "Don't Know" inside numeric columns)
- Peer-group ranking and quartiling with `groupby().rank()` and `pd.qcut`, the pandas equivalents of SQL `RANK()` and `NTILE()`
- Survey-weighted statistics (weighted mean and median) instead of naive averages
- Mean vs median reasoning for right-skewed data
- Regression with `statsmodels` (OLS and survey-weighted WLS, robust standard errors)
- Charts with matplotlib, unit tests with pytest

## Key findings
1. **The mean hides the real story.** In Manufacturing, mean sales per employee *fell* from $46.6k (2014) to $39.9k (2025), but the median *rose* 45%, from $20.7k to $30.1k. A few very large firms drag the mean.
2. **Services productivity rose sharply.** Median sales per employee went from $10.8k to $23.5k (+117%) between 2014 and 2025.
3. **Survey weights matter.** The weighted median for Manufacturing 2022 is $12.4k versus $20.4k unweighted, because small firms are under-sampled relative to their population share.
4. **Bigger and more capital-intensive firms are more productive.** In the Manufacturing regression, a 10% increase in capital per employee goes with about 2.5% higher sales per employee (WLS: about 1.5%), and firm size has a positive elasticity of about 0.2.
5. **After controlling for size, sales per employee in 2025 is about 30% higher than in 2014 for Manufacturing and about 99% higher for Services** (OLS, USD terms).
6. **Labor cost share falls as productivity rises.** Median labor cost / sales in Manufacturing drops from 21.6% in the bottom productivity quartile to 3.8% in the top quartile.
7. **Services labor cost share fell from 0.208 to 0.101 (median) between 2014 and 2025.** The drop is visible in mean, median and weighted measures, so it is not driven by a few outliers. Still, treat it with care: the 2025 round has no missing labor cost values at all, so survey design or data processing may differ from earlier rounds.

![Sales per employee](figures/01_sales_per_employee_boxplot.png)
![Mean vs median](figures/02_mean_vs_median.png)
![Labor cost ratio](figures/03_labor_cost_ratio.png)

## Repository structure
| Path | Purpose |
|---|---|
| `data/India_Productivity_Dataset_Renamed.csv` | Raw source data |
| `productivity_pandas.py` | Loads, cleans and analyses the data (all reusable functions) |
| `analysis.py` | Runs everything: tables, charts, regressions |
| `tests/test_productivity.py` | pytest suite (toy-data unit tests and real-data sanity checks) |
| `outputs/` | Generated tables (CSV) and regression results |
| `figures/` | Generated charts |
| `requirements.txt` | Dependencies |

## How to run
```bash
pip install -r requirements.txt
python productivity_pandas.py     # prints the sector/year report
python analysis.py                # regenerates tables, figures, regressions
python -m pytest                  # runs the tests
```

Interactive use (e.g. in a notebook):
```python
from productivity_pandas import build_report
df_clean, report = build_report()
report
```

## Analyses included
| Function | What it does |
|---|---|
| `top10_productive()` / `bottom10_productive()` | Top/bottom 10 firms per sector/year by value added per employee (`groupby().rank()`) |
| `avg_labor_cost_ratio()` | Labor cost to sales ratio by sector/year (mean, median, weighted mean) |
| `productivity_quartiles()` | Quartiles of sales per employee within each sector (`pd.qcut`) |
| `outlier_rates()` | Share of firms flagged by the survey's built-in outlier checks |
| `sector_year_report()` | One table: coverage, mean/median/weighted-median productivity, labor cost ratio |
| `weighted_mean()` / `weighted_median()` | Survey-weighted statistics |

## Sector / year report
| sector | year | firms surveyed | with productivity | mean sales/emp | median sales/emp | weighted median | mean VA/emp | median labor cost/sales |
|---|---|---|---|---|---|---|---|---|
| Manufacturing | 2014 | 7,163 | 6,837 | 46,572 | 20,749 | 18,526 | 17,449 | 0.111 |
| Manufacturing | 2022 | 5,417 | 4,699 | 44,887 | 20,387 | 12,422 | 20,947 | 0.103 |
| Manufacturing | 2025 | 5,708 | 5,696 | 39,916 | 30,055 | 25,916 | 18,410 | 0.090 |
| Services | 2014 | 2,118 | 1,944 | 34,088 | 10,807 | 7,608 | n/a | 0.208 |
| Services | 2022 | 3,959 | 3,938 | 35,742 | 12,619 | 10,342 | n/a | 0.170 |
| Services | 2025 | 4,771 | 4,768 | 37,070 | 23,495 | 22,959 | n/a | 0.101 |

Productivity figures are in USD (see "Units and data notes"). Full table with more columns: `outputs/sector_year_report.csv`.

## Units and data notes
- **Units.** `sales_per_employee` and `value_added_per_employee` are in USD: local currency converted at the survey-year exchange rate (`exchange_rate`) and deflated with `usd_deflator`. No extra deflating is needed to compare years, but USD values are sensitive to the exchange rate (INR went from about 55 per USD in 2014 to about 85 in 2025), so part of any change reflects currency movement.
- **Value added is Manufacturing only.** `value_added_per_employee` is blank for every Services row (the calculation needs fixed assets, which Services firms were not asked about), and only about 92% of Manufacturing firms have it. The code returns `NaN` rather than a wrong number.
- **Survey weights.** `sample_weight` ranges from 1 to about 102,000. Weighted statistics are reported next to unweighted ones. Weights are extreme, so the WLS regressions are a robustness check, not the headline.
- **Survey rounds.** The 2022 round covers two reference years (2021 and 2022).
- **Outlier flags are not comparable across years.** About 12% of Manufacturing firms are flagged in 2022 against 0.3% in 2025, which suggests different cleaning rules between rounds.
- **Regressions are associations, not causal effects.** Year effects also mix in composition changes in who was sampled.

### Column names in the original World Bank files
| Renamed | Original code |
|---|---|
| `firm_id` | `idstd` |
| `sample_weight` | `wt` |
| `sales` | `d2` |
| `labor_cost` | `n2a` |
| `raw_material_cost` | `n2e` |
| `inventory` | `n2i` |
| `employees` | `l1` |
| `fixed_assets` | `n7a` |

## Tech
Python 3, pandas, numpy, matplotlib, statsmodels, pytest. No database: all analysis runs on in-memory DataFrames.

