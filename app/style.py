"""Look and feel of the dashboard: CSS, banner and KPI cards."""
import streamlit as st

CSS = """
<style>
.block-container {padding-top: 1.6rem;}
.banner {background: linear-gradient(120deg, #1F5FBF 0%, #2D8CCF 100%);
         border-radius: 16px; padding: 22px 28px; color: white; margin-bottom: 18px;}
.banner-title {font-size: 1.9rem; font-weight: 700; line-height: 1.2;}
.banner-sub {margin-top: 6px; opacity: 0.92; font-size: 1rem;}
.chip {display: inline-block; background: rgba(255,255,255,0.18); border-radius: 999px;
       padding: 3px 12px; font-size: 0.8rem; margin: 10px 8px 0 0;}
.kpi-card {background: #F1F5FB; border-radius: 14px; padding: 14px 16px;
           border-left: 6px solid #1F5FBF; margin-bottom: 12px; min-height: 118px;}
.kpi-alert {border-left-color: #D64545;}
.kpi-good {border-left-color: #2E9E6B;}
.kpi-label {font-size: 0.85rem; color: #4A5A75; font-weight: 600;}
.kpi-value {font-size: 1.9rem; font-weight: 700; color: #1B2A41; line-height: 1.2; margin-top: 4px;}
.kpi-note {font-size: 0.8rem; color: #6B7A92; margin-top: 2px;}
.section-note {color: #6B7A92; font-size: 0.9rem; margin: -6px 0 10px 0;}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def banner(title, subtitle, chips):
    chip_html = "".join(f'<span class="chip">{c}</span>' for c in chips)
    st.markdown(
        f'<div class="banner"><div class="banner-title">{title}</div>'
        f'<div class="banner-sub">{subtitle}</div>{chip_html}</div>',
        unsafe_allow_html=True,
    )


def kpi_card(icon, label, value, note="", tone="neutral"):
    """tone: 'neutral' (blue), 'alert' (red) or 'good' (green)."""
    tone_class = {"alert": " kpi-alert", "good": " kpi-good"}.get(tone, "")
    return (
        f'<div class="kpi-card{tone_class}">'
        f'<div class="kpi-label">{icon} {label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-note">{note}</div></div>'
    )