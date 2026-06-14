"""
Page 3: Seasonal Efficiency Comparison
"""

import streamlit as st
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from components.charts import seasonal_comparison_chart, yearly_trend_chart
from kpis import kpis_by_group

st.set_page_config(page_title="Seasonal Comparison", page_icon="🌤️", layout="wide")
st.title("🌤️ Seasonal & Temporal Efficiency Comparison")

if "filtered_df" not in st.session_state:
    st.warning("Please set filters on the main page first.")
    st.stop()

df = st.session_state["filtered_df"]
full_df = st.session_state["full_df"]

if len(df) == 0:
    st.warning("No data for the selected filters.")
    st.stop()

kpi_choice = st.selectbox(
    "Select KPI to compare",
    ["Capacity Utilization Ratio", "Congestion Pressure Index (%)",
     "Idle Capacity Percentage (%)", "Operational Variability Score"]
)

st.subheader("By Season")
season_kpis = kpis_by_group(df, "season")
c1, c2 = st.columns([2, 1])
with c1:
    st.plotly_chart(seasonal_comparison_chart(season_kpis, "season", kpi_choice),
                     use_container_width=True)
with c2:
    st.dataframe(season_kpis, use_container_width=True)

st.markdown("---")
st.subheader("Weekday vs Weekend")
weekend_kpis = kpis_by_group(df, "is_weekend")
weekend_kpis["is_weekend"] = weekend_kpis["is_weekend"].map({True: "Weekend", False: "Weekday"})
c1, c2 = st.columns([2, 1])
with c1:
    st.plotly_chart(seasonal_comparison_chart(weekend_kpis, "is_weekend", kpi_choice),
                     use_container_width=True)
with c2:
    st.dataframe(weekend_kpis, use_container_width=True)

if "time_band" in df.columns:
    st.markdown("---")
    st.subheader("Time-of-Day Band (Morning / Afternoon / Evening / Night)")
    band_kpis = kpis_by_group(df, "time_band")
    c1, c2 = st.columns([2, 1])
    with c1:
        st.plotly_chart(seasonal_comparison_chart(band_kpis, "time_band", kpi_choice),
                         use_container_width=True)
    with c2:
        st.dataframe(band_kpis, use_container_width=True)

st.markdown("---")
st.subheader("Year-over-Year Trend (2015-2025)")
st.caption("Computed on the full dataset (ignores date filter) to show the complete long-term trend.")
st.plotly_chart(yearly_trend_chart(full_df, "Total Activity Load"), use_container_width=True)

st.markdown("---")
st.subheader("KPIs by Year")
year_kpis = kpis_by_group(full_df, "year")
st.dataframe(year_kpis, use_container_width=True)
