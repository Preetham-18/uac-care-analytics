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