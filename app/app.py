"""UAC Care System Analytics: dashboard (version 3, interactive)."""
import sys
from datetime import date
from pathlib import Path

# Let the app find the `src` and `app` folders when started with `streamlit run app/app.py`
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app"))

import numpy as np
import streamlit as st

from src.charts import (backlog_chart, cbp_hhs_chart, cbp_share_chart, cumulative_chart,
                        load_overview_chart, net_intake_chart)
from src.kpis import compute_kpis
from src.metrics import list_flag_windows
from src.pipeline import build_dataset
from style import banner, inject_css, kpi_card

st.set_page_config(page_title="UAC Care System Analytics", page_icon="📊", layout="wide")
inject_css()


@st.cache_data
def load_data():
    return build_dataset()


df = load_data()
reported = df[df["is_reported"]]
first_day = reported.index.min().date()
last_day = reported.index.max().date()


def clamp(start, end):
    return max(first_day, start), min(last_day, end)


def longest_window(flag_col):
    windows = list_flag_windows(df, flag_col)
    best = windows.sort_values("reports").iloc[-1]
    return best["start"], best["end"]


PRESETS = {
    "All": (first_day, last_day),
    "2023": clamp(date(2023, 1, 1), date(2023, 12, 31)),
    "2024": clamp(date(2024, 1, 1), date(2024, 12, 31)),
    "2025": clamp(date(2025, 1, 1), date(2025, 12, 31)),
    "Longest strain": longest_window("strain_flag"),
    "Longest relief": longest_window("relief_flag"),
}


def set_range(start, end):
    st.session_state["date_range"] = (start, end)


# ---------- Sidebar ----------
st.sidebar.header("Filters")
st.sidebar.caption("Quick select")
st.session_state.setdefault("date_range", (first_day, last_day))
left, right = st.sidebar.columns(2)
for i, (label, (p_start, p_end)) in enumerate(PRESETS.items()):
    (left if i % 2 == 0 else right).button(
        label, on_click=set_range, args=(p_start, p_end), width="stretch", key=f"preset_{label}")

picked = st.sidebar.date_input(
    "Date range", min_value=first_day, max_value=last_day, key="date_range")

GRANULARITY = {"Daily": "D", "Weekly": "W", "Monthly": "M"}
granularity_label = st.sidebar.radio("Time view", list(GRANULARITY), horizontal=True)
granularity = GRANULARITY[granularity_label]

st.sidebar.caption("Chart layers (Overview)")
layers = st.sidebar.multiselect(
    "Show on the load chart",
    ["Daily line", "7-day average", "14-day average", "Strain and relief bands"],
    default=["Daily line", "7-day average", "14-day average", "Strain and relief bands"],
    help="The daily line and rolling averages appear in the Daily view only.",
)

if len(picked) != 2:
    st.info("Pick an end date to complete the range.")
    st.stop()
start, end = picked

kpis = compute_kpis(df, start, end)
if kpis["reports"] == 0 or np.isnan(kpis["reports"]):
    st.warning("There are no reported days in this range. Try a wider range.")
    st.stop()

# ---------- Banner ----------
banner(
    "UAC Care System Analytics",
    "How many children are in federal care, and is the system under strain?",
    [
        f"📅 {start:%d %b %Y} to {end:%d %b %Y}",
        f"🗂 {int(kpis['reports'])} reported days",
        f"👁 {granularity_label} view",
        "Source: HHS daily reporting, CBP and HHS",
    ],
)

tab_overview, tab_compare, tab_flow = st.tabs(
    ["📊 Overview", "⚖️ CBP vs HHS", "🔄 Net intake and backlog"]
)
in_range = reported.loc[str(start):str(end)]

# ---------- Tab 1: Overview ----------
with tab_overview:
    change = kpis["total_children_change"]
    c1, c2, c3 = st.columns(3)
    c1.markdown(
        kpi_card("🧒", "Total children under care", f"{kpis['total_children_under_care']:,.0f}",
                 f"{change:+,.0f} over the range", "alert" if change > 0 else "good"),
        unsafe_allow_html=True)
    c2.markdown(
        kpi_card("⚖️", "Net intake pressure", f"{kpis['net_intake_pressure']:+,.1f}",
                 "children per reported day · flow-based"),
        unsafe_allow_html=True)
    c3.markdown(
        kpi_card("📈", "Care load volatility index", f"{kpis['volatility_index']:.2f} %",
                 "average 14-day swing around the average"),
        unsafe_allow_html=True)

    c4, c5, c6 = st.columns(3)
    c4.markdown(
        kpi_card("📦", "Backlog accumulation rate", f"{kpis['backlog_accumulation_rate']:+,.1f}",
                 "children per calendar day · flow-based"),
        unsafe_allow_html=True)
    c5.markdown(
        kpi_card("🔁", "Discharge offset ratio", f"{kpis['discharge_offset_ratio']:.2f}",
                 "discharges per child transferred in · flow-based"),
        unsafe_allow_html=True)
    c6.markdown(
        kpi_card("⏳", "Reports in sustained backlog", f"{kpis['backlog_report_share_pct']:.1f} %",
                 "5+ reports in a row with more in than out"),
        unsafe_allow_html=True)

    st.plotly_chart(
        load_overview_chart(
            df, start, end, granularity=granularity,
            show_daily="Daily line" in layers,
            show_7d="7-day average" in layers,
            show_14d="14-day average" in layers,
            show_windows="Strain and relief bands" in layers),
        width="stretch")
    st.markdown(
        '<div class="section-note">Red bands: sustained strain (14-day average in the top 25% of '
        'its own history). Green bands: sustained relief (bottom 25%). These are relative to '
        'these three years, not an official capacity limit.</div>',
        unsafe_allow_html=True)

    with st.expander("How to read the cards"):
        st.markdown(
            """
- **Total children under care**: CBP custody + HHS care on the last reported day of the range.
- **Net intake pressure**: average (transfers into HHS - discharges) per reported day. Positive means more entering than leaving.
- **Volatility index**: how far the load swings around its 14-day average (higher = less stable).
- **Backlog accumulation rate**: total net intake divided by calendar days in the range.
- **Discharge offset ratio**: discharges per child transferred in. Below 1 means discharges are not keeping up.
- **Caution:** the cards marked *flow-based* did not match the real change in headcount during 2023,
  and the data does not explain why. Read them next to the first card.
            """
        )

# ---------- Tab 2: CBP vs HHS ----------
with tab_compare:
    cbp = in_range["cbp_custody"].astype(float)
    hhs = in_range["hhs_care"].astype(float)
    a, b, c = st.columns(3)
    a.markdown(kpi_card("🏥", "Average HHS care", f"{hhs.mean():,.0f}", "children per reported day"),
               unsafe_allow_html=True)
    b.markdown(kpi_card("🛂", "Average CBP custody", f"{cbp.mean():,.0f}", "children per reported day"),
               unsafe_allow_html=True)
    c.markdown(kpi_card("🥧", "CBP share of all children", f"{cbp.sum() / (cbp.sum() + hhs.sum()) * 100:.1f} %",
                        "HHS holds the rest"), unsafe_allow_html=True)
    st.plotly_chart(cbp_hhs_chart(df, start, end, granularity=granularity), width="stretch")
    st.plotly_chart(cbp_share_chart(df, start, end), width="stretch")

# ---------- Tab 3: Net intake and backlog ----------
with tab_flow:
    net = in_range["net_daily_intake"].astype(float)
    more_in_pct = (net > 0).mean() * 100
    care_backlog_pct = in_range["backlog_flag_care"].astype("float64").mean() * 100
    d1, d2, d3 = st.columns(3)
    d1.markdown(kpi_card("📥", "Reports with more in than out", f"{more_in_pct:.1f} %",
                         "net intake above zero · flow-based"), unsafe_allow_html=True)
    d2.markdown(kpi_card("⏳", "Sustained backlog (net intake)", f"{kpis['backlog_report_share_pct']:.1f} %",
                         "5+ reports in a row with positive net intake"), unsafe_allow_html=True)
    d3.markdown(kpi_card("🏥", "Sustained backlog (HHS care rising)", f"{care_backlog_pct:.1f} %",
                         "5+ reports in a row where HHS care grew"), unsafe_allow_html=True)

    st.plotly_chart(net_intake_chart(df, start, end, granularity=granularity), width="stretch")
    st.plotly_chart(cumulative_chart(df, start, end), width="stretch")
    st.markdown(
        '<div class="section-note">If the orange and blue lines drift apart, the transfers and '
        'discharges in the data do not explain the change in HHS care. This happens strongly in '
        '2023, and the data does not tell us why.</div>',
        unsafe_allow_html=True)
    st.plotly_chart(backlog_chart(df, start, end), width="stretch")