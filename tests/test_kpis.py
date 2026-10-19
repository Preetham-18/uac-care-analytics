import numpy as np
import pandas as pd

from src.kpis import compute_kpis


def make_df():
    # Jan 3 is unreported, so the range spans 4 calendar days but has 3 reports
    idx = pd.date_range("2024-01-01", "2024-01-04", freq="D", name="date")
    df = pd.DataFrame(index=idx)
    df["total_system_load"] = pd.array([100, 110, pd.NA, 130], dtype="Int64")
    df["net_daily_intake"] = pd.array([10, -4, pd.NA, 6], dtype="Int64")
    df["cbp_transferred"] = pd.array([20, 10, pd.NA, 30], dtype="Int64")
    df["hhs_discharged"] = pd.array([10, 14, pd.NA, 24], dtype="Int64")
    df["volatility_index_14d"] = [2.0, 3.0, np.nan, 1.0]
    df["backlog_flag_intake"] = pd.array([True, False, pd.NA, True], dtype="boolean")
    df["is_reported"] = [True, True, False, True]
    return df


def test_total_children_is_latest_reported_load():
    k = compute_kpis(make_df())
    assert k["total_children_under_care"] == 130
    assert k["total_children_change"] == 30


def test_net_intake_pressure_is_average_per_reported_day():
    assert compute_kpis(make_df())["net_intake_pressure"] == 4      # (10 - 4 + 6) / 3


def test_backlog_rate_uses_calendar_days():
    assert compute_kpis(make_df())["backlog_accumulation_rate"] == 3.0   # 12 / 4 days


def test_discharge_offset_ratio():
    assert compute_kpis(make_df())["discharge_offset_ratio"] == 0.8      # 48 / 60


def test_volatility_and_backlog_share():
    k = compute_kpis(make_df())
    assert k["volatility_index"] == 2.0
    assert round(k["backlog_report_share_pct"], 2) == 66.67


def test_date_range_selects_reports():
    k = compute_kpis(make_df(), "2024-01-02", "2024-01-04")
    assert k["reports"] == 2
    assert k["total_children_under_care"] == 130


def test_empty_range_returns_nan_not_error():
    k = compute_kpis(make_df(), "2030-01-01", "2030-12-31")
    assert np.isnan(k["total_children_under_care"])


def test_zero_transfers_gives_empty_ratio():
    df = make_df()
    df["cbp_transferred"] = pd.array([0, 0, pd.NA, 0], dtype="Int64")
    assert np.isnan(compute_kpis(df)["discharge_offset_ratio"])