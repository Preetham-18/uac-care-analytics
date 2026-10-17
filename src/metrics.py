"""Derived healthcare capacity metrics for the UAC care system."""

import pandas as pd
from pandas import DataFrame


def add_total_system_load(df):
    """Total children under federal care: CBP custody + HHS care."""
    df = df.copy()
    df["total_system_load"] = df["cbp_custody"] + df["hhs_care"]
    return df


def add_net_daily_intake(df):
    """Children entering HHS minus children leaving HHS in a day.

    Positive  -> HHS is receiving more than it releases (load builds up).
    Negative  -> HHS is releasing more than it receives (load eases).
    """
    df = df.copy()
    df["net_daily_intake"] = df["cbp_transferred"] - df["hhs_discharged"]
    return df


def add_core_metrics(df):
    """Add every Day 6 metric in one call."""
    df = add_total_system_load(df)
    df = add_net_daily_intake(df)
    return df


def add_growth_rate(df):
    """Change in Total System Load versus the previous *reported* day.

    - days_since_prev_report : calendar days between the two reports
    - load_growth_pct        : % change since the previous report
    - load_growth_pct_per_day: the same, divided by the days between reports,
                               so a 3-day change is not compared with a 1-day one
    Unreported days stay empty. A previous load of 0 gives an empty result
    (no division by zero).
    """
    df = df.copy()
    reported = df[df["is_reported"]]
    previous = reported["total_system_load"].shift(1)
    days = reported.index.to_series().diff().dt.days
    growth = (reported["total_system_load"] - previous) / previous.where(previous > 0) * 100
    df["days_since_prev_report"] = days
    df["load_growth_pct"] = growth
    df["load_growth_pct_per_day"] = growth / days
    return df


def add_cumulative_net_intake(df):
    """Running total of Net Daily Intake over the reported days.

    Also adds the *actual* change in HHS care since the first report, and the
    difference between the two (the part the flows do not explain).
    """
    df = df.copy()
    df["cumulative_net_intake"] = df["net_daily_intake"].cumsum()
    first_hhs = df.loc[df["is_reported"], "hhs_care"].iloc[0]
    df["hhs_change_since_start"] = df["hhs_care"] - first_hhs
    df["unexplained_change"] = df["hhs_change_since_start"] - df["cumulative_net_intake"]
    return df


def _run_length(condition):
    """For every True, how many True values in a row so far (0 for False)."""
    run_id = (~condition).cumsum()
    return condition.groupby(run_id).cumsum()


def add_backlog_indicators(df, min_streak=5):
    """Flag sustained pressure, measured two ways.

    Streaks are counted over *reported* days only, so the regular Friday and
    Saturday gaps do not break a streak.

    - positive_intake_streak : consecutive reports with Net Daily Intake > 0
    - rising_care_streak     : consecutive reports where HHS care rose
    - backlog_flag_intake    : positive_intake_streak >= min_streak (official)
    - backlog_flag_care      : rising_care_streak >= min_streak (cross-check)
    Unreported days stay empty.
    """
    df = df.copy()
    reported = df[df["is_reported"]]
    hhs_change = reported["hhs_care"].diff()

    intake_positive = (reported["net_daily_intake"] > 0).fillna(False).astype(bool)
    care_rising = (hhs_change > 0).fillna(False).astype(bool)

    df["hhs_change_since_prev"] = hhs_change
    df["positive_intake_streak"] = _run_length(intake_positive).astype("Int64")
    df["rising_care_streak"] = _run_length(care_rising).astype("Int64")
    df["backlog_flag_intake"] = df["positive_intake_streak"] >= min_streak
    df["backlog_flag_care"] = df["rising_care_streak"] >= min_streak
    return df


def add_rolling_metrics(df, windows=(7, 14), min_reports=3):
    """Rolling averages and the Care Load Volatility Index.

    Windows are measured in CALENDAR days (e.g. the last 7 days), but only
    reported days take part, so a window normally holds 4 to 5 reports.
    A window with fewer than `min_reports` reports is left empty, so a
    "7-day average" is never built from one or two isolated reports.

    For each window w (in days) this adds:
    - load_avg_{w}d        : rolling mean of Total System Load
    - net_intake_avg_{w}d  : rolling mean of Net Daily Intake
    - load_std_{w}d        : rolling standard deviation of Total System Load
    - volatility_index_{w}d: std / mean * 100  (the Care Load Volatility Index,
                             in percent; higher = less stable)
    """
    df = df.copy()
    reported = df[df["is_reported"]]
    load = reported["total_system_load"].astype("float64")
    net = reported["net_daily_intake"].astype("float64")

    for w in windows:
        load_roll = load.rolling(f"{w}D", min_periods=min_reports)
        df[f"load_avg_{w}d"] = load_roll.mean()
        df[f"load_std_{w}d"] = load_roll.std()
        df[f"net_intake_avg_{w}d"] = net.rolling(f"{w}D", min_periods=min_reports).mean()
        df[f"volatility_index_{w}d"] = (
            df[f"load_std_{w}d"] / df[f"load_avg_{w}d"].where(df[f"load_avg_{w}d"] > 0) * 100
        )
    return df


def _label_sustained(condition, min_reports):
    """True for every report that sits inside a run of at least min_reports Trues."""
    run_id = (~condition).cumsum()
    run_size = condition.groupby(run_id).transform("sum")
    return condition & (run_size >= min_reports)


def compute_thresholds(df, avg_col="load_avg_14d", high_q=0.75, low_q=0.25):
    """Load levels that separate strain (high) and relief (low) from normal."""
    avg = df.loc[df["is_reported"], avg_col].dropna()
    return avg.quantile(high_q), avg.quantile(low_q)


def add_strain_relief(df, avg_col="load_avg_14d", high_q=0.75, low_q=0.25, min_reports=7):
    """Mark sustained strain and relief windows.

    strain_flag : the rolling average stays above the high threshold
                  (75th percentile by default) for at least min_reports reports
    relief_flag : the rolling average stays below the low threshold
                  (25th percentile by default) for at least min_reports reports
    Thresholds are relative to this dataset's own history (no official
    capacity figure is available). Unreported days stay empty.
    """
    df = df.copy()
    high_cut, low_cut = compute_thresholds(df, avg_col, high_q, low_q)
    reported = df[df["is_reported"]]
    avg = reported[avg_col]

    strain = _label_sustained((avg > high_cut).astype(bool), min_reports)
    relief = _label_sustained((avg < low_cut).astype(bool), min_reports)
    df["strain_flag"] = strain.reindex(df.index).astype("boolean")
    df["relief_flag"] = relief.reindex(df.index).astype("boolean")
    return df


def list_flag_windows(df, flag_col):
    """One row per window of consecutive flagged reports."""
    reported = df[df["is_reported"]]
    flag = reported[flag_col].fillna(False).astype(bool)
    run_id = (~flag).cumsum()
    rows = []
    for _, run in reported[flag].groupby(run_id[flag]):
        rows.append({
            "start": run.index[0].date(),
            "end": run.index[-1].date(),
            "reports": len(run),
            "calendar_days": (run.index[-1] - run.index[0]).days + 1,
            "avg_total_load": round(run["total_system_load"].astype(float).mean()),
        })
    return pd.DataFrame(rows, columns=["start", "end", "reports", "calendar_days", "avg_total_load"])