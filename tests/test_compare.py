import pandas as pd

from src.compare import compare_periods, early_late_periods, summarize_range


def make_df():
    idx = pd.date_range("2024-01-01", periods=5, freq="D", name="date")
    cbp = [10, 20, 30, 40, 50]
    hhs = [90, 180, 270, 360, 450]
    df = pd.DataFrame(index=idx)
    df["cbp_custody"] = pd.array(cbp, dtype="Int64")
    df["hhs_care"] = pd.array(hhs, dtype="Int64")
    df["total_system_load"] = df["cbp_custody"] + df["hhs_care"]
    for col in ["apprehended", "cbp_transferred", "hhs_discharged", "net_daily_intake"]:
        df[col] = pd.array([1] * 5, dtype="Int64")
    df["volatility_index_14d"] = 2.0
    df["strain_flag"] = pd.array([False, False, True, True, True], dtype="boolean")
    df["relief_flag"] = pd.array([True, True, False, False, False], dtype="boolean")
    df["is_reported"] = True
    return df


def test_average_of_a_date_range():
    out = summarize_range(make_df(), "2024-01-01", "2024-01-02")
    assert out["avg_total_load"] == 150          # mean of 100 and 200
    assert out["reports"] == 2


def test_cbp_share_is_cbp_over_total():
    out = summarize_range(make_df(), "2024-01-01", "2024-01-05")
    assert round(out["cbp_share_pct"], 2) == 10.0


def test_early_and_late_halves_do_not_overlap():
    p = early_late_periods(make_df())
    assert p["early"] == (pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-03"))
    assert p["late"] == (pd.Timestamp("2024-01-04"), pd.Timestamp("2024-01-05"))


def test_share_of_reports_in_strain():
    out = compare_periods(make_df(), early_late_periods(make_df()))
    assert out.loc["strain_pct", "late"] == 100.0
    assert out.loc["relief_pct", "early"] > 0