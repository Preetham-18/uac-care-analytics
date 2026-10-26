"""Plotly charts for the dashboard (pure functions: data in, figure out)."""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.metrics import list_flag_windows
from src.trends import summarize_by_period

COLORS = {
    "blue": "#1F5FBF",
    "light_blue": "#7FB2F0",
    "orange": "#F28C28",
    "gray": "#B8C2D0",
    "red": "#D64545",
    "green": "#2E9E6B",
    "ink": "#1B2A41",
}


def _style(fig, height=420):
    """The look shared by every chart."""
    fig.update_layout(
        template="plotly_white",
        height=height,
        hovermode="x unified",
        margin=dict(l=10, r=10, t=60, b=10),
        legend=dict(orientation="h", y=-0.12, x=0),
        font=dict(family="Segoe UI, Roboto, Arial, sans-serif", color=COLORS["ink"]),
        title=dict(x=0.0, font=dict(size=18)),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#E6ECF5")
    return fig


def _in_range(df, start, end):
    part = df.loc[start:end]
    return part[part["is_reported"]]


def _clipped_windows(df, flag_col, start, end):
    """Flag windows that overlap the chosen range, cut to the range."""
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    clipped = []
    for _, w in list_flag_windows(df, flag_col).iterrows():
        w_start, w_end = pd.Timestamp(w["start"]), pd.Timestamp(w["end"])
        if w_end < s or w_start > e:
            continue
        clipped.append((max(w_start, s), min(w_end, e)))
    return clipped


def _legend_square(fig, name, color):
    """vrect shapes have no legend entry, so add an invisible point that has one."""
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode="markers", name=name,
        marker=dict(size=12, color=color, symbol="square", opacity=0.45),
    ))


GRANULARITY_LABELS = {"D": "Daily", "W": "Weekly average", "M": "Monthly average"}


def _summary(df, start, end, granularity):
    """Averages per period for the chosen range (edge periods use only in-range reports)."""
    return summarize_by_period(df.loc[start:end], granularity)


def load_overview_chart(df, start, end, granularity="D", show_daily=True,
                        show_7d=True, show_14d=True, show_windows=True):
    """Total System Load with rolling averages and strain/relief windows.

    Rolling averages are daily-level ideas, so they appear only for granularity "D".
    For weekly and monthly views the line shows the average of each period.
    """
    fig = go.Figure()
    if granularity == "D":
        part = _in_range(df, start, end)
        if show_daily:
            fig.add_trace(go.Scatter(
                x=part.index, y=part["total_system_load"].astype(float), mode="lines",
                name="Daily total load", line=dict(color=COLORS["gray"], width=1.5)))
        if show_7d:
            fig.add_trace(go.Scatter(
                x=part.index, y=part["load_avg_7d"], mode="lines",
                name="7-day average", line=dict(color=COLORS["light_blue"], width=2)))
        if show_14d:
            fig.add_trace(go.Scatter(
                x=part.index, y=part["load_avg_14d"], mode="lines",
                name="14-day average", line=dict(color=COLORS["blue"], width=3)))
    else:
        t = _summary(df, start, end, granularity)
        fig.add_trace(go.Scatter(
            x=t.index, y=t["total_system_load"], mode="lines+markers",
            name=GRANULARITY_LABELS[granularity],
            line=dict(color=COLORS["blue"], width=3), marker=dict(size=5)))
    if show_windows:
        for flag_col, color, label in [("strain_flag", COLORS["red"], "Strain window"),
                                       ("relief_flag", COLORS["green"], "Relief window")]:
            windows = _clipped_windows(df, flag_col, start, end)
            for w_start, w_end in windows:
                fig.add_vrect(x0=w_start, x1=w_end, fillcolor=color, opacity=0.13,
                              layer="below", line_width=0)
            if windows:
                _legend_square(fig, label, color)
    fig.update_layout(title="Total system load (CBP custody + HHS care)",
                      yaxis_title="Children under care")
    return _style(fig)


def cbp_hhs_chart(df, start, end, granularity="D"):
    """CBP and HHS in two panels (their sizes differ about 40 times)."""
    part = _summary(df, start, end, granularity)
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
        subplot_titles=("HHS care: children in care shelters",
                        "CBP custody: children held at the border"))
    fig.add_trace(go.Scatter(
        x=part.index, y=part["hhs_care"].astype(float), mode="lines", name="HHS care",
        line=dict(color=COLORS["blue"], width=2), fill="tozeroy",
        fillcolor="rgba(31,95,191,0.12)"), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=part.index, y=part["cbp_custody"].astype(float), mode="lines", name="CBP custody",
        line=dict(color=COLORS["orange"], width=2), fill="tozeroy",
        fillcolor="rgba(242,140,40,0.15)"), row=2, col=1)
    fig.update_layout(showlegend=False)
    return _style(fig, height=560)


def cbp_share_chart(df, start, end):
    """CBP's share of all children under care, with a 14-day average."""
    part = _in_range(df, start, end)
    cbp = part["cbp_custody"].astype(float)
    total = part["total_system_load"].astype(float)
    share = cbp / total * 100
    smooth = share.rolling("14D", min_periods=3).mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=share.index, y=share, mode="lines", name="Daily share",
                             line=dict(color=COLORS["gray"], width=1.5)))
    fig.add_trace(go.Scatter(x=smooth.index, y=smooth, mode="lines", name="14-day average",
                             line=dict(color=COLORS["orange"], width=3)))
    fig.update_layout(title="CBP custody as a share of all children under care",
                      yaxis_title="% of total")
    return _style(fig, height=340)


def net_intake_chart(df, start, end, granularity="W"):
    """Average net intake per reported day: more in than out, or more out than in."""
    t = _summary(df, start, end, granularity)
    net = t["net_daily_intake"]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=t.index, y=net.where(net > 0), name="More in than out",
                         marker_color=COLORS["orange"]))
    fig.add_trace(go.Bar(x=t.index, y=net.where(net <= 0), name="More out than in",
                         marker_color=COLORS["light_blue"]))
    fig.add_hline(y=0, line_color=COLORS["gray"], line_width=1)
    fig.update_layout(
        barmode="overlay",
        title=f"Net intake: transfers into HHS minus discharges ({GRANULARITY_LABELS[granularity].lower()})",
        yaxis_title="Children per reported day")
    return _style(fig, height=360)


def cumulative_chart(df, start, end):
    """Running total of net intake vs the real change in HHS care, both starting at 0."""
    part = _in_range(df, start, end)
    net = part["net_daily_intake"].astype(float)
    cumulative = net.cumsum() - net.iloc[0]
    hhs = part["hhs_care"].astype(float)
    actual = hhs - hhs.iloc[0]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=part.index, y=cumulative, mode="lines",
                             name="Running total of net intake (transfers - discharges)",
                             line=dict(color=COLORS["orange"], width=3)))
    fig.add_trace(go.Scatter(x=part.index, y=actual, mode="lines",
                             name="Actual change in HHS care",
                             line=dict(color=COLORS["blue"], width=3)))
    fig.add_hline(y=0, line_color=COLORS["gray"], line_width=1)
    fig.update_layout(title="Do the flows explain the change in HHS care?",
                      yaxis_title="Children, change since start of range")
    return _style(fig, height=380)


def backlog_chart(df, start, end):
    """HHS care line with the reports flagged as sustained backlog (two definitions)."""
    part = _in_range(df, start, end)
    hhs = part["hhs_care"].astype(float)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=part.index, y=hhs, mode="lines", name="HHS care",
                             line=dict(color=COLORS["gray"], width=2)))
    for col, label, color in [("backlog_flag_care", "HHS care rising 5+ reports in a row", COLORS["blue"]),
                              ("backlog_flag_intake", "Net intake positive 5+ reports in a row", COLORS["orange"])]:
        flagged = part[part[col].fillna(False).astype(bool)]
        fig.add_trace(go.Scatter(x=flagged.index, y=flagged["hhs_care"].astype(float), mode="markers",
                                 name=label, marker=dict(size=7, color=color)))
    fig.update_layout(title="Sustained backlog: two ways of measuring it", yaxis_title="Children in HHS care")
    return _style(fig, height=380)