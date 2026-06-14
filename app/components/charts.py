"""
charts.py
==========
Reusable Plotly chart-building functions for the Streamlit dashboard.
Keeping these separate from the page files keeps the pages short and
focused on layout/filters.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def capacity_timeline_chart(df: pd.DataFrame, value_col: str = "OLI") -> go.Figure:
    """
    Line chart of OLI (or another metric) over time, with a horizontal
    reference line for the congestion threshold (0.75) and idle
    threshold for visual context.
    """
    fig = px.line(
        df, x="Timestamp", y=value_col,
        title=f"Capacity Utilization Timeline ({value_col})",
        labels={value_col: "Operational Load Index (OLI)", "Timestamp": "Date / Time"},
    )
    fig.add_hline(y=0.75, line_dash="dash", line_color="red",
                   annotation_text="Congestion threshold", annotation_position="top left")
    fig.update_layout(height=450, hovermode="x unified")
    return fig


def activity_load_chart(df: pd.DataFrame) -> go.Figure:
    """
    Line chart of raw Sales Count, Redemption Count, and Total Activity
    Load over time.
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Timestamp"], y=df["Sales Count"],
                              name="Sales Count", line=dict(width=1)))
    fig.add_trace(go.Scatter(x=df["Timestamp"], y=df["Redemption Count"],
                              name="Redemption Count", line=dict(width=1)))
    fig.add_trace(go.Scatter(x=df["Timestamp"], y=df["Total Activity Load"],
                              name="Total Activity Load", line=dict(width=2, dash="dot")))
    fig.update_layout(title="Sales, Redemption & Total Activity Load",
                       height=450, hovermode="x unified",
                       xaxis_title="Date / Time", yaxis_title="Ticket Count")
    return fig


def congestion_idle_heatmap(df: pd.DataFrame, value_col: str = "OLI") -> go.Figure:
    """
    Heatmap of average `value_col` by day-of-week (rows) vs hour-of-day
    (columns). Useful for spotting recurring congestion / idle windows.
    """
    pivot = df.pivot_table(
        index="day_name", columns="hour", values=value_col, aggfunc="mean"
    )

    # Order days Monday -> Sunday
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pivot = pivot.reindex([d for d in day_order if d in pivot.index])

    fig = px.imshow(
        pivot, aspect="auto", color_continuous_scale="RdYlGn_r",
        labels=dict(x="Hour of Day", y="Day of Week", color=value_col),
        title=f"Congestion / Idle Heatmap (avg {value_col} by day & hour)",
    )
    fig.update_layout(height=450)
    return fig


def seasonal_comparison_chart(kpi_df: pd.DataFrame, group_col: str,
                               kpi_col: str = "Capacity Utilization Ratio") -> go.Figure:
    """
    Bar chart comparing a KPI across groups (e.g. seasons, years,
    weekday vs weekend).
    """
    fig = px.bar(
        kpi_df, x=group_col, y=kpi_col,
        title=f"{kpi_col} by {group_col}",
        text_auto=".3f",
        color=kpi_col, color_continuous_scale="Blues",
    )
    fig.update_layout(height=400)
    return fig


def yearly_trend_chart(daily_df: pd.DataFrame, value_col: str = "Total Activity Load") -> go.Figure:
    """
    Monthly-aggregated trend line across all years (2015-2025) to show
    long-term shifts (e.g. COVID-era dip in 2020).
    """
    df = daily_df.copy()
    df["year_month"] = df["Timestamp"].dt.to_period("M").dt.to_timestamp()
    monthly = df.groupby("year_month", as_index=False)[value_col].sum()

    fig = px.line(
        monthly, x="year_month", y=value_col,
        title=f"Monthly {value_col} Trend (2015-2025)",
        labels={"year_month": "Month", value_col: value_col},
    )
    fig.update_layout(height=450)
    return fig


def idle_vs_congested_pie(df: pd.DataFrame) -> go.Figure:
    """
    Pie chart showing proportion of intervals that are idle, congested,
    or normal.
    """
    total = len(df)
    idle = df["is_idle"].sum() if "is_idle" in df.columns else 0
    congested = df["is_congested"].sum() if "is_congested" in df.columns else 0
    normal = total - idle - congested
    normal = max(normal, 0)

    fig = px.pie(
        names=["Normal", "Idle", "Congested"],
        values=[normal, idle, congested],
        title="Interval Classification",
        color=["Normal", "Idle", "Congested"],
        color_discrete_map={"Normal": "#88c999", "Idle": "#aab2c0", "Congested": "#e07a5f"},
    )
    fig.update_layout(height=400)
    return fig
