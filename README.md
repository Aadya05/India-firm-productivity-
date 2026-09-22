# India Firm Productivity — Pandas Analysis Project

A Python/pandas portfolio project analyzing firm-level productivity data from
India (World Bank Enterprise Survey style data), covering **29,136 firms**
across three survey years (2014, 2022, 2025) and two sectors (Manufacturing,
Services).

## What this project demonstrates
- Loading and type-cleaning a real-world, messily-formatted CSV with pandas
- Building a clean, analysis-ready DataFrame from raw staged data
- Peer-group ranking and quartiling (`groupby().rank()`, `pd.qcut`) — the
  pandas equivalents of SQL window functions (`RANK`, `NTILE`)
- Aggregate reporting (`groupby().agg()`) for cost-structure and
  data-quality analysis
- A reusable reporting function suitable for feeding a dashboard or
  further analysis (e.g. matplotlib/plotly, Streamlit)

## Files
| File | Purpose |
|---|---|
| `India_Productivity_Dataset_Renamed.csv` | Raw source data |
| `productivity_pandas.py` | Loads the CSV, cleans it, and runs all analysis functions |
| `README.md` | This file |

## How to run
```bash
python3 productivity_pandas.py
```
This prints the row count of the cleaned data and the
`sector_year_productivity_report` table.

To use interactively (e.g. in a notebook):
```python
from productivity_pandas import build_report
df_clean, report = build_report("India_Productivity_Dataset_Renamed.csv")
report
```

## Analyses included
1. **Top 10 most productive firms** per sector/year (by value added per
   employee) — `top10_productive()`
2. **Bottom 10 least productive firms** per sector/year — `bottom10_productive()`
3. **Average labor-cost-to-sales ratio** by sector and year —
   `avg_labor_cost_ratio()`
4. **Productivity quartiles** (`pd.qcut`) of sales-per-employee within each
   sector — `productivity_quartiles()`
5. **Outlier rate** by sector/year, based on the dataset's built-in outlier
   flags — `outlier_rates()`
6. **`sector_year_report()`** — a single function combining firm counts,
   average productivity, and average labor cost ratio

## Sample result — sector/year productivity report

| sector | year | firms | avg sales/employee | avg VA/employee | avg labor cost/sales | avg employees |
|---|---|---|---|---|---|---|
| Manufacturing | 2014 | 6,837 | 46,572 | 17,449 | 0.129 | 88.8 |
| Manufacturing | 2022 | 4,699 | 44,887 | 20,947 | 0.152 | 123.4 |
| Manufacturing | 2025 | 5,696 | 39,916 | 18,410 | 0.110 | 108.0 |
| Services | 2014 | 1,944 | 34,088 | — | 0.284 | 91.6 |
| Services | 2022 | 3,938 | 35,742 | — | 0.218 | 49.3 |
| Services | 2025 | 4,768 | 37,070 | — | 0.134 | 56.6 |

## Known data quirk
`value_added_per_employee` is blank for every Services-sector row in the
source data (Services firms weren't surveyed on fixed assets, which the
value-added calculation depends on). This is a property of the raw survey,
not a loading bug — `build_clean()` and every downstream function handle it
correctly by returning `NaN` rather than a wrong number.

## Tech
Python 3, pandas, numpy. No database — all analysis runs on in-memory
DataFrames.

## Requirements
```
pandas
numpy
```
