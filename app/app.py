"""UAC Care System Analytics: dashboard (version 1)."""
import sys
from pathlib import Path

# Let the app find the `src` folder when started with `streamlit run app/app.py`
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import streamlit as st

from src.kpis import compute_kpis
from src.pipeline import build_dataset

st.set_page_config(page_title="UAC Care System Analytics", page_icon="📊", layout="wide")


@st.cache_data
def load_data():
    return build_dataset()


df = load_data()
reported = df[df["is_reported"]]

# ---------- Sidebar ----------
st.sidebar.header("Filters")
first_day = reported.index.min().date()
last_day = reported.index.max().date()
picked = st.sidebar.date_input(
    "Date range",
    value=(first_day, last_day),
    min_value=first_day,
    max_value=last_day,
)
if len(picked) != 2:
    st.info("Pick an end date to complete the range.")
    st.stop()
start, end = picked

# ---------- Header ----------
st.title("UAC Care System Analytics")
st.caption("Children in CBP custody and HHS care: daily reporting, Jan 2023 to Dec 2025")

kpis = compute_kpis(df, start, end)
if kpis["reports"] == 0 or np.isnan(kpis["reports"]):
    st.warning("There are no reported days in this range. Try a wider range.")
    st.stop()

st.caption(f"Showing {int(kpis['reports'])} reported days from {start:%d %b %Y} to {end:%d %b %Y}")

# ---------- KPI cards ----------
row1 = st.columns(3)
row1[0].metric(
    "Total children under care",
    f"{kpis['total_children_under_care']:,.0f}",
    delta=f"{kpis['total_children_change']:+,.0f} over the range",
    delta_color="inverse",  # more children = more pressure, so an increase shows red
)
row1[1].metric("Net intake pressure", f"{kpis['net_intake_pressure']:+,.1f} / day")
row1[2].metric("Care load volatility index", f"{kpis['volatility_index']:.2f} %")

row2 = st.columns(3)
row2[0].metric("Backlog accumulation rate", f"{kpis['backlog_accumulation_rate']:+,.1f} / day")
row2[1].metric("Discharge offset ratio", f"{kpis['discharge_offset_ratio']:.2f}")
row2[2].metric("Reports in sustained backlog", f"{kpis['backlog_report_share_pct']:.1f} %")

with st.expander("How to read these cards"):
    st.markdown(
        """
- **Total children under care**: CBP custody + HHS care on the last reported day of the range.
- **Net intake pressure**: average (transfers into HHS - discharges) per reported day. Positive = more entering than leaving.
- **Volatility index**: how far the load swings around its 14-day average (higher = less stable).
- **Backlog accumulation rate**: total net intake divided by calendar days in the range.
- **Discharge offset ratio**: discharges per child transferred in. Below 1 = discharges are not keeping up.
- **Caution:** the three flow-based cards (net intake, backlog rate, discharge ratio) did not
  match the real change in headcount during 2023, and the data does not explain why.
  Always read them next to the first card.
        """
    )

# ---------- A first chart (proper charts arrive on Day 15) ----------
st.subheader("Total system load")
in_range = reported.loc[str(start):str(end)]
st.line_chart(in_range["total_system_load"].astype(float))