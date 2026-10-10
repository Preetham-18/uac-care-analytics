"""Derived healthcare capacity metrics for the UAC care system."""


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