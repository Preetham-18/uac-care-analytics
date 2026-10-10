import pandas as pd

from src.metrics import add_core_metrics
from src.metrics import add_cumulative_net_intake, add_growth_rate


def make_row(cbp_custody, hhs_care, transferred, discharged):
    return pd.DataFrame(
        {
            "cbp_custody": [cbp_custody],
            "hhs_care": [hhs_care],
            "cbp_transferred": [transferred],
            "hhs_discharged": [discharged],
        }
    ).astype("Int64")


def test_total_system_load_is_cbp_plus_hhs():
    out = add_core_metrics(make_row(500, 4000, 300, 250))
    assert out["total_system_load"].iloc[0] == 4500


def test_net_daily_intake_is_transfers_minus_discharges():
    out = add_core_metrics(make_row(500, 4000, 300, 250))
    assert out["net_daily_intake"].iloc[0] == 50


def test_unreported_day_stays_empty():
    row = pd.DataFrame(
        {
            "cbp_custody": [pd.NA],
            "hhs_care": [pd.NA],
            "cbp_transferred": [pd.NA],
            "hhs_discharged": [pd.NA],
        }
    ).astype("Int64")
    out = add_core_metrics(row)
    assert pd.isna(out["total_system_load"].iloc[0])
    assert pd.isna(out["net_daily_intake"].iloc[0])


def make_daily():
    idx = pd.date_range("2024-01-01", "2024-01-04", freq="D", name="date")
    df = pd.DataFrame(
        {
            "total_system_load": pd.array([100, pd.NA, pd.NA, 120], dtype="Int64"),
            "net_daily_intake": pd.array([10, pd.NA, pd.NA, -4], dtype="Int64"),
            "hhs_care": pd.array([90, pd.NA, pd.NA, 100], dtype="Int64"),
            "is_reported": [True, False, False, True],
        },
        index=idx,
    )
    return df


def test_growth_uses_previous_reported_day_and_gap():
    out = add_growth_rate(make_daily())
    last = out.iloc[3]
    assert last["days_since_prev_report"] == 3
    assert round(last["load_growth_pct"], 2) == 20.0
    assert round(last["load_growth_pct_per_day"], 2) == 6.67
    assert pd.isna(out.iloc[1]["load_growth_pct"])      # unreported day stays empty


def test_growth_with_zero_previous_load_is_empty():
    df = make_daily()
    df.loc["2024-01-01", "total_system_load"] = 0
    out = add_growth_rate(df)
    assert pd.isna(out.iloc[3]["load_growth_pct"])


def test_cumulative_net_intake_skips_unreported_days():
    out = add_cumulative_net_intake(make_daily())
    assert out.iloc[0]["cumulative_net_intake"] == 10
    assert out.iloc[3]["cumulative_net_intake"] == 6
    assert out.iloc[3]["hhs_change_since_start"] == 10
    assert out.iloc[3]["unexplained_change"] == 4