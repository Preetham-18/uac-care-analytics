"""The five headline KPIs, calculated for any date range."""
import numpy as np
import pandas as pd


def compute_kpis(df, start=None, end=None):
    """Headline KPIs for the reported days between start and end (inclusive).

    Needs the columns added by add_core_metrics, add_rolling_metrics and
    add_backlog_indicators. Returns a dict, so the dashboard can show each
    value on a card. An empty range returns empty (NaN) values, not an error.
    """
    part = df.loc[start:end]
    part = part[part["is_reported"]]
    if part.empty:
        return {k: np.nan for k in KPI_KEYS}

    load = part["total_system_load"].astype("float64")
    transferred = part["cbp_transferred"].astype("float64").sum()
    discharged = part["hhs_discharged"].astype("float64").sum()
    calendar_days = (part.index[-1] - part.index[0]).days + 1

    return {
        # 1. Total Children Under Care: where the system stands at the end of the range
        "total_children_under_care": load.iloc[-1],
        "total_children_change": load.iloc[-1] - load.iloc[0],
        # 2. Net Intake Pressure: typical daily imbalance (children per reported day)
        "net_intake_pressure": part["net_daily_intake"].astype("float64").mean(),
        # 3. Care Load Volatility Index: average 14-day swing (%)
        "volatility_index": part["volatility_index_14d"].astype("float64").mean(),
        # 4. Backlog Accumulation Rate: children added per calendar day
        "backlog_accumulation_rate": part["net_daily_intake"].astype("float64").sum() / calendar_days,
        "backlog_report_share_pct": part["backlog_flag_intake"].astype("float64").mean() * 100,
        # 5. Discharge Offset Ratio: discharges per child transferred in
        "discharge_offset_ratio": discharged / transferred if transferred > 0 else np.nan,
        "reports": len(part),
    }


KPI_KEYS = [
    "total_children_under_care", "total_children_change", "net_intake_pressure",
    "volatility_index", "backlog_accumulation_rate", "backlog_report_share_pct",
    "discharge_offset_ratio", "reports",
]