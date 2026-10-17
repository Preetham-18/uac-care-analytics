import pandas as pd
import pytest
from src.metrics import add_core_metrics
from src.metrics import add_cumulative_net_intake, add_growth_rate
from src.metrics import add_backlog_indicators
from src.trends import summarize_by_period
from src.metrics import add_rolling_metrics



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


def make_backlog_df(net=(5, pd.NA, pd.NA, 3, 2)):
    idx = pd.date_range("2024-01-04", periods=5, freq="D", name="date")  # Thu to Mon
    return pd.DataFrame(
        {
            "net_daily_intake": pd.array(list(net), dtype="Int64"),
            "hhs_care": pd.array([100, pd.NA, pd.NA, 110, 120], dtype="Int64"),
            "is_reported": [True, False, False, True, True],
        },
        index=idx,
    )


def test_streak_is_not_broken_by_unreported_days():
    out = add_backlog_indicators(make_backlog_df(), min_streak=3)
    assert out.iloc[4]["positive_intake_streak"] == 3
    assert out.iloc[4]["backlog_flag_intake"] == True  # noqa: E712


def test_negative_day_resets_the_streak():
    out = add_backlog_indicators(make_backlog_df(net=(5, pd.NA, pd.NA, -3, 2)), min_streak=3)
    assert out.iloc[4]["positive_intake_streak"] == 1
    assert out.iloc[4]["backlog_flag_intake"] == False  # noqa: E712


def test_unreported_days_have_no_flag():
    out = add_backlog_indicators(make_backlog_df(), min_streak=3)
    assert pd.isna(out.iloc[1]["backlog_flag_intake"])


def test_rising_care_streak_counts_reports_where_hhs_grew():
    out = add_backlog_indicators(make_backlog_df(), min_streak=3)
    assert out.iloc[0]["rising_care_streak"] == 0     # no previous report
    assert out.iloc[4]["rising_care_streak"] == 2



def make_df():
    # Sun 2024-01-07 .. Sat 2024-01-13, then Sun 2024-01-14
    idx = pd.date_range("2024-01-07", "2024-01-14", freq="D", name="date")
    reported = [True, True, True, True, True, False, False, True]
    df = pd.DataFrame(index=idx)
    for col in ["cbp_custody", "hhs_care", "total_system_load",
                "apprehended", "cbp_transferred", "hhs_discharged", "net_daily_intake"]:
        df[col] = pd.array([10, 20, 30, 40, 50, pd.NA, pd.NA, 100], dtype="Int64")
    df["is_reported"] = reported
    return df


def test_weekly_mean_uses_only_reported_days():
    out = summarize_by_period(make_df(), "W")
    assert len(out) == 2
    assert out.iloc[0]["hhs_care"] == 30        # mean of 10..50, not diluted by gaps
    assert out.iloc[0]["reported_days"] == 5


def test_sunday_starts_a_new_week():
    out = summarize_by_period(make_df(), "W")
    assert out.index[1] == pd.Timestamp("2024-01-14")
    assert out.iloc[1]["reported_days"] == 1


def test_monthly_groups_by_calendar_month():
    out = summarize_by_period(make_df(), "M")
    assert len(out) == 1
    assert out.iloc[0]["reported_days"] == 6


def test_invalid_granularity_raises():
    with pytest.raises(ValueError):
        summarize_by_period(make_df(), "Y")


def make_rolling_df(dates, loads):
    idx = pd.DatetimeIndex(pd.to_datetime(dates), name="date")
    return pd.DataFrame(
        {
            "total_system_load": pd.array(loads, dtype="Int64"),
            "net_daily_intake": pd.array([1] * len(loads), dtype="Int64"),
            "is_reported": [True] * len(loads),
        },
        index=idx,
    )


def test_rolling_average_needs_enough_reports():
    df = make_rolling_df(pd.date_range("2024-01-01", periods=5), [10, 20, 30, 40, 50])
    out = add_rolling_metrics(df, windows=(7,), min_reports=3)
    assert pd.isna(out.iloc[1]["load_avg_7d"])          # only 2 reports so far
    assert out.iloc[2]["load_avg_7d"] == 20             # mean of 10, 20, 30
    assert out.iloc[4]["load_avg_7d"] == 30             # mean of all five


def test_window_is_measured_in_calendar_days():
    dates = ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-12"]
    out = add_rolling_metrics(make_rolling_df(dates, [10, 20, 30, 40]), windows=(7,), min_reports=3)
    assert pd.isna(out.iloc[3]["load_avg_7d"])          # isolated report after a long gap


def test_volatility_index_is_std_over_mean_in_percent():
    df = make_rolling_df(pd.date_range("2024-01-01", periods=3), [10, 20, 30])
    out = add_rolling_metrics(df, windows=(7,), min_reports=3)
    assert round(out.iloc[2]["volatility_index_7d"], 2) == 50.0   # std 10 / mean 20


def test_unreported_days_stay_empty_in_rolling_columns():
    df = make_rolling_df(pd.date_range("2024-01-01", periods=4), [10, 20, 30, 40])
    df.loc["2024-01-04", ["total_system_load", "net_daily_intake"]] = pd.NA
    df.loc["2024-01-04", "is_reported"] = False
    out = add_rolling_metrics(df, windows=(7,), min_reports=3)
    assert pd.isna(out.iloc[3]["load_avg_7d"])


from src.metrics import add_strain_relief, list_flag_windows


def make_strain_df(avgs):
    idx = pd.date_range("2024-01-01", periods=len(avgs), name="date")
    return pd.DataFrame(
        {
            "total_system_load": pd.array([100] * len(avgs), dtype="Int64"),
            "load_avg_14d": [float(a) for a in avgs],
            "is_reported": [True] * len(avgs),
        },
        index=idx,
    )


def test_short_high_run_is_not_strain():
    # 3 high values in a row, but we require 4
    df = make_strain_df([1, 1, 1, 1, 1, 1, 100, 100, 100, 1, 1, 1])
    out = add_strain_relief(df, high_q=0.5, low_q=0.0, min_reports=4)
    assert not out["strain_flag"].fillna(False).any()


def test_long_high_run_is_strain_and_listed_once():
    df = make_strain_df([1, 1, 1, 1, 1, 1, 100, 100, 100, 100, 1, 1])
    out = add_strain_relief(df, high_q=0.5, low_q=0.0, min_reports=4)
    windows = list_flag_windows(out, "strain_flag")
    assert len(windows) == 1
    assert windows.iloc[0]["reports"] == 4


def test_low_run_is_relief():
    df = make_strain_df([100, 100, 100, 100, 100, 100, 1, 1, 1, 1, 100, 100])
    out = add_strain_relief(df, high_q=1.0, low_q=0.4, min_reports=4)
    assert out["relief_flag"].fillna(False).sum() == 4