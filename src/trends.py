"""Daily, weekly and monthly trend summaries of the care system."""
import pandas as pd

STOCK_COLS = ["cbp_custody", "hhs_care", "total_system_load"]
FLOW_COLS = ["apprehended", "cbp_transferred", "hhs_discharged", "net_daily_intake"]

# Reports come Sunday to Thursday, so weeks run Sunday to Saturday ("W-SAT").
# The default pandas week ends on Sunday and would split the reporting week.
PERIOD_RULES = {"W": "W-SAT", "M": "M"}


def summarize_by_period(df, granularity="W"):
    """Average of every stock and flow per reported day, for each period.

    granularity: "D" (each reported day), "W" (Sun-Sat week), "M" (month).
    Averages are used, not sums, because unreported days would make sums
    depend on how many days happened to be reported in the period.
    reported_days says how many reports each average is based on.
    """
    if granularity not in ("D", *PERIOD_RULES):
        raise ValueError("granularity must be 'D', 'W' or 'M'")

    reported = df[df["is_reported"]]
    cols = STOCK_COLS + FLOW_COLS
    values = reported[cols].astype("float64")

    if granularity == "D":
        out = values.copy()
        out["reported_days"] = 1
        return out

    grouped = values.groupby(reported.index.to_period(PERIOD_RULES[granularity]))
    out = grouped.mean()
    out["reported_days"] = grouped.size()
    out.index = out.index.to_timestamp()
    out.index.name = "period_start"
    return out