import numpy as np
import pandas as pd

from src.charts import cbp_hhs_chart, cbp_share_chart, load_overview_chart


def make_df():
    idx = pd.date_range("2024-01-01", "2024-01-20", freq="D", name="date")
    n = len(idx)
    df = pd.DataFrame(index=idx)
    df["cbp_custody"] = pd.array([10] * n, dtype="Int64")
    df["hhs_care"] = pd.array([90] * n, dtype="Int64")
    df["total_system_load"] = df["cbp_custody"] + df["hhs_care"]
    df["load_avg_7d"] = 100.0
    df["load_avg_14d"] = 100.0
    df["is_reported"] = True
    strain = [False] * n
    for i in range(5, 10):          # Jan 6 to Jan 10
        strain[i] = True
    df["strain_flag"] = pd.array(strain, dtype="boolean")
    df["relief_flag"] = pd.array([False] * n, dtype="boolean")
    return df


def test_each_strain_window_becomes_one_shaded_band():
    fig = load_overview_chart(make_df(), "2024-01-01", "2024-01-20")
    assert len(fig.layout.shapes) == 1


def test_windows_can_be_switched_off():
    fig = load_overview_chart(make_df(), "2024-01-01", "2024-01-20", show_windows=False)
    assert len(fig.layout.shapes) == 0


def test_averages_can_be_switched_off():
    with_avg = load_overview_chart(make_df(), "2024-01-01", "2024-01-20", show_windows=False)
    without = load_overview_chart(make_df(), "2024-01-01", "2024-01-20",
                                  show_averages=False, show_windows=False)
    assert len(with_avg.data) == 3 and len(without.data) == 1


def test_band_is_cut_to_the_chosen_range():
    fig = load_overview_chart(make_df(), "2024-01-08", "2024-01-20")
    assert pd.Timestamp(fig.layout.shapes[0].x0) == pd.Timestamp("2024-01-08")


def test_window_outside_range_is_not_drawn():
    fig = load_overview_chart(make_df(), "2024-01-12", "2024-01-20")
    assert len(fig.layout.shapes) == 0


def test_cbp_hhs_chart_has_one_panel_each():
    fig = cbp_hhs_chart(make_df(), "2024-01-01", "2024-01-20")
    assert len(fig.data) == 2
    assert fig.data[0].y[0] == 90 and fig.data[1].y[0] == 10


def test_cbp_share_is_cbp_over_total():
    fig = cbp_share_chart(make_df(), "2024-01-01", "2024-01-20")
    assert np.isclose(fig.data[0].y[0], 10.0)