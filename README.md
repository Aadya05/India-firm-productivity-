# India Firm Productivity — SQL Reporting Project

A SQL portfolio project analyzing firm-level productivity data from India
(World Bank Enterprise Survey style data), covering **29,136 firms** across
three survey years (2014, 2022, 2025) and two sectors (Manufacturing,
Services).

## What this project demonstrates
- Loading a real-world, messily-typed CSV into a relational database
- Building a clean, typed view on top of raw staged data
- Window functions (`RANK`, `NTILE`) for peer-group ranking and quartiling
- Aggregate reporting (`GROUP BY`, `CASE WHEN`) for cost-structure and
  data-quality analysis
- A reusable reporting view suitable for feeding a BI tool (Tableau/Power BI)

## Files
| File | Purpose |
|---|---|
| `India_Productivity_Dataset_Renamed.csv` | Raw source data |
| `load_data.py` | Loads the CSV into `firms.db` (SQLite) and runs `project.sql` |
| `project.sql` | Schema, clean view, and all analytical queries |
| `README.md` | This file |

## How to run
```bash
python3 load_data.py
```
This creates `firms.db`. Then explore it with any SQLite client, e.g.:
```bash
sqlite3 firms.db
sqlite> SELECT * FROM sector_year_productivity_report;
```

## Queries included
1. **Top 10 most productive firms** per sector/year (by value added per employee)
2. **Bottom 10 least productive firms** per sector/year
3. **Average labor-cost-to-sales ratio** by sector and year
4. **Productivity quartiles** (`NTILE(4)`) of sales-per-employee within each sector
5. **Outlier rate** by sector/year, based on the dataset's built-in outlier flags
6. **`sector_year_productivity_report`** — a single reporting view combining
   firm counts, average productivity, and average labor cost ratio

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
not a loading bug — the `firms_clean` view and queries handle it correctly
by returning `NULL` rather than a wrong number.

## Tech
SQLite (queries are portable to Postgres/MySQL with trivial changes —
mainly `NULLIF`/`CAST` syntax).
