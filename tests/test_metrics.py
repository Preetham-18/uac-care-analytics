import pandas as pd

from src.metrics import add_core_metrics


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