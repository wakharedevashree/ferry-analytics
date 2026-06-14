"""
Page 1: Capacity Utilization Timeline
"""

import streamlit as st
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from components.charts import capacity_timeline_chart, activity_load_chart

st.set_page_config(page_title="Capacity Timeline", page_icon="📈", layout="wide")
st.title("📈 Capacity Utilization Timeline")

if "filtered_df" not in st.session_state:
    st.warning("Please set filters on the main page first.")
    st.stop()

df = st.session_state["filtered_df"]
resolution = st.session_state["resolution"]

if len(df) == 0:
    st.warning("No data for the selected filters.")
    st.stop()

st.markdown(
    f"Showing **{len(df):,}** intervals at **{resolution}** resolution. "
    "The dashed red line marks the congestion threshold (OLI ≥ 0.75)."
)

st.plotly_chart(capacity_timeline_chart(df, "OLI"), use_container_width=True)
st.plotly_chart(activity_load_chart(df), use_container_width=True)

st.markdown("---")
st.subheader("Raw data preview")
display_cols = ["Timestamp", "Sales Count", "Redemption Count",
                 "Total Activity Load", "Redemption Pressure Ratio",
                 "OLI", "is_idle", "is_congested"]
display_cols = [c for c in display_cols if c in df.columns]
st.dataframe(df[display_cols].head(500), use_container_width=True)
