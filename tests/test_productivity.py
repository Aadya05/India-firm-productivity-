import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import productivity_pandas as pp  # noqa: E402


# ------------------------------------------------------------ toy data tests
def toy_df():
    rows = []
    for i in range(20):
        rows.append(dict(
            firm_id=i, sector="Manufacturing", survey_year=2014,
            sales_per_employee=float(i + 1), value_added_per_employee=float(i + 1) / 2,
            labor_cost_sales_ratio=0.1, sample_weight=1.0, employees=10.0, any_outlier=(i == 0),
        ))
    for i in range(20, 30):
        rows.append(dict(
            firm_id=i, sector="Services", survey_year=2014,
            sales_per_employee=float(i), value_added_per_employee=np.nan,
            labor_cost_sales_ratio=0.2, sample_weight=1.0, employees=5.0, any_outlier=False,
        ))
    df = pd.DataFrame(rows)
    df["sector"] = pd.Categorical(df["sector"], categories=["Manufacturing", "Services"])
    return df


def test_weighted_median_simple():
    assert pp.weighted_median([1, 2, 3], [1, 1, 1]) == 2
    # heavy weight on the largest value pulls the median up to it
    assert pp.weighted_median([1, 2, 3], [1, 1, 10]) == 3


def test_weighted_mean_ignores_nan():
    assert pp.weighted_mean([1, np.nan, 3], [1, 5, 1]) == 2


def test_top10_returns_at_most_10_per_group_and_skips_nan_services():
    top = pp.top10_productive(toy_df())
    assert top.groupby(["sector", "survey_year"], observed=True).size().max() <= 10
    assert "Services" not in set(top["sector"].astype(str))  # Services VA is NaN


def test_top10_is_ranked_descending():
    top = pp.top10_productive(toy_df(), metric="sales_per_employee")
    mfg = top[top["sector"] == "Manufacturing"]
    assert mfg["sales_per_employee"].is_monotonic_decreasing
    assert mfg["sales_per_employee"].iloc[0] == 20.0


def test_bottom10_is_ranked_ascending():
    bot = pp.bottom10_productive(toy_df(), metric="sales_per_employee")
    mfg = bot[bot["sector"] == "Manufacturing"]
    assert mfg["sales_per_employee"].is_monotonic_increasing
    assert mfg["sales_per_employee"].iloc[0] == 1.0


def test_quartiles_are_balanced_within_sector():
    q = pp.productivity_quartiles(toy_df())
    counts = q[q["sector"] == "Manufacturing"]["productivity_quartile"].value_counts()
    assert set(counts.index) == {"Q1", "Q2", "Q3", "Q4"}
    assert counts.max() - counts.min() <= 1


def test_outlier_rate_between_0_and_1():
    r = pp.outlier_rates(toy_df())
    assert r["outlier_rate"].between(0, 1).all()
    mfg = r[r["sector"] == "Manufacturing"].iloc[0]
    assert mfg["flagged"] == 1 and mfg["firms"] == 20


# ------------------------------------------------------------ real-data tests
@pytest.fixture(scope="module")
def real():
    if not pp.DATA_PATH.exists():
        pytest.skip("dataset not found in data/")
    raw = pp.load_raw()
    return raw, pp.build_clean(raw)


def test_no_rows_lost_and_ids_unique(real):
    raw, clean = real
    assert len(clean) == len(raw) == 29136
    assert clean["firm_id"].is_unique


def test_services_value_added_stays_nan(real):
    _, clean = real
    assert clean.loc[clean["sector"] == "Services", "value_added_per_employee"].isna().all()


def test_three_years_two_sectors(real):
    _, clean = real
    assert set(clean["survey_year"]) == {2014, 2022, 2025}
    assert set(clean["sector"].astype(str)) == {"Manufacturing", "Services"}


def test_numeric_columns_are_numeric(real):
    _, clean = real
    for col in pp.NUMERIC_COLS:
        assert pd.api.types.is_numeric_dtype(clean[col]), col


def test_sales_per_employee_positive(real):
    _, clean = real
    assert (clean["sales_per_employee"].dropna() > 0).all()


def test_report_matches_known_values(real):
    _, clean = real
    rep = pp.sector_year_report(clean).set_index(["sector", "survey_year"])
    assert rep.loc[("Manufacturing", 2014), "firms_with_productivity"] == 6837
    assert rep.loc[("Services", 2025), "firms_with_productivity"] == 4768
    assert round(rep.loc[("Manufacturing", 2014), "avg_sales_per_employee"]) == 46572
