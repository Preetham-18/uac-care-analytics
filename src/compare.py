"""Compare time periods, and CBP against HHS."""
import pandas as pd


def early_late_periods(df):
    """Split the reporting history into two equal halves of calendar time."""
    reported_dates = df.index[df["is_reported"]]
    first, last = reported_dates.min(), reported_dates.max()
    midpoint = (first + (last - first) / 2).normalize()
    return {
        "early": (first, midpoint),
        "late": (midpoint + pd.Timedelta(days=1), last),
    }


def summarize_range(df, start, end):
    """Key numbers for the reported days between start and end (inclusive)."""
    part = df.loc[start:end]
    part = part[part["is_reported"]]
    f = lambda col: part[col].astype("float64")
    return pd.Series({
        "reports": len(part),
        "avg_total_load": f("total_system_load").mean(),
        "peak_total_load": f("total_system_load").max(),
        "avg_cbp_custody": f("cbp_custody").mean(),
        "avg_hhs_care": f("hhs_care").mean(),
        "cbp_share_pct": f("cbp_custody").sum() / f("total_system_load").sum() * 100,
        "avg_apprehended": f("apprehended").mean(),
        "avg_transferred": f("cbp_transferred").mean(),
        "avg_discharged": f("hhs_discharged").mean(),
        "avg_net_intake": f("net_daily_intake").mean(),
        "avg_volatility_14d": f("volatility_index_14d").mean(),
        "strain_pct": part["strain_flag"].astype("float64").mean() * 100,
        "relief_pct": part["relief_flag"].astype("float64").mean() * 100,
    })


def compare_periods(df, periods):
    """One column per period. periods = {"name": (start, end), ...}."""
    return pd.DataFrame({name: summarize_range(df, s, e) for name, (s, e) in periods.items()})


def yearly_periods(df):
    """One (start, end) pair per calendar year present in the data."""
    years = sorted(set(df.index[df["is_reported"]].year))
    return {str(y): (f"{y}-01-01", f"{y}-12-31") for y in years}