"""
app.py
=======
Main entry point for the Ferry Capacity Utilization & Operational
Efficiency Analytics dashboard.

Run with:
    streamlit run app/app.py
"""

import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from components.data_utils import load_data, filter_data
from components.charts import idle_vs_congested_pie, capacity_timeline_chart
from kpis import compute_all_kpis


st.set_page_config(
    page_title="Ferry Capacity Analytics",
    page_icon="🚢",
    layout="wide",
)

st.title("🚢 Ferry Capacity Utilization & Operational Efficiency Analytics")
st.caption("Jack Layton Ferry Terminal → Centre Island, Hanlan's Point, Ward's Island | 2015-2025")

# ---------------------------------------------------------------------
# SIDEBAR FILTERS (shared across pages via session_state)
# ---------------------------------------------------------------------
st.sidebar.header("Filters")

granularity = st.sidebar.radio(
    "Granularity", ["15-min", "Hourly", "Daily"], index=1,
    help="Controls the time resolution used across all dashboard pages."
)
resolution_map = {"15-min": "15min", "Hourly": "hourly", "Daily": "daily"}
resolution = resolution_map[granularity]

df = load_data(resolution)

min_date = df["Timestamp"].min().date()
max_date = df["Timestamp"].max().date()

date_range = st.sidebar.date_input(
    "Date range", value=(min_date, max_date),
    min_value=min_date, max_value=max_date
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

season_options = sorted(df["season"].unique().tolist())
seasons = st.sidebar.multiselect("Season", season_options, default=season_options)

only_operating = st.sidebar.checkbox("Only show operating intervals", value=True)

# Store filtered data + resolution in session_state for other pages
filtered = filter_data(df, start_date, end_date, seasons, only_operating)
st.session_state["filtered_df"] = filtered
st.session_state["resolution"] = resolution
st.session_state["full_df"] = df

# ---------------------------------------------------------------------
# KPI SUMMARY CARDS
# ---------------------------------------------------------------------
st.subheader("📊 KPI Summary")

if len(filtered) == 0:
    st.warning("No data for the selected filters. Adjust date range or season selection.")
else:
    kpis = compute_all_kpis(filtered)

    col1, col2, col3, col4, col5 = st.columns(5)

    util = kpis["Capacity Utilization Ratio"]
    col1.metric("Capacity Utilization Ratio", f"{util:.1%}",
                 help="Average OLI across operating intervals. Higher = busier relative to typical peak for that hour.")

    congestion = kpis["Congestion Pressure Index (%)"]
    col2.metric("Congestion Pressure Index", f"{congestion:.2f}%",
                 help="% of intervals with OLI >= 0.75 (over-utilized).")

    idle = kpis["Idle Capacity Percentage (%)"]
    col3.metric("Idle Capacity %", f"{idle:.2f}%",
                 help="% of intervals in sustained low-activity (under-utilized) runs.")

    strain = kpis["Peak Strain Duration (minutes)"]
    col4.metric("Peak Strain Duration", f"{strain:.0f} min",
                 help="Longest consecutive run of congested intervals.")

    variability = kpis["Operational Variability Score"]
    col5.metric("Operational Variability", f"{variability:.2f}",
                 help="Coefficient of variation of Total Activity Load (std/mean). Higher = less predictable.")

    # Threshold-based alerts
    st.markdown("---")
    alert_cols = st.columns(3)
    if congestion > 5:
        alert_cols[0].error(f"⚠️ High congestion: {congestion:.1f}% of intervals over-utilized")
    else:
        alert_cols[0].success(f"✅ Congestion within normal range ({congestion:.1f}%)")

    if idle > 30:
        alert_cols[1].error(f"⚠️ High idle capacity: {idle:.1f}% of intervals under-utilized")
    else:
        alert_cols[1].success(f"✅ Idle capacity within normal range ({idle:.1f}%)")

    if variability > 2:
        alert_cols[2].warning(f"⚠️ High variability score: {variability:.2f} (unstable demand)")
    else:
        alert_cols[2].success(f"✅ Variability stable ({variability:.2f})")

    # Overview charts
    st.markdown("---")
    c1, c2 = st.columns([2, 1])
    with c1:
        st.plotly_chart(capacity_timeline_chart(filtered), use_container_width=True)
    with c2:
        st.plotly_chart(idle_vs_congested_pie(filtered), use_container_width=True)

st.markdown("---")
st.markdown(
    """
    ### 📁 Dashboard Navigation
    Use the sidebar pages to explore:
    - **Capacity Timeline** — detailed OLI / activity trends over time
    - **Heatmaps** — congestion & idle patterns by day/hour
    - **Seasonal Comparison** — weekday vs weekend, seasonal efficiency
    - **KPI Summary** — full KPI breakdown table by group
    """
)
