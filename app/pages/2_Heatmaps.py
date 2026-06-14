


"""
Page 2: Congestion & Idle Period Heatmaps
"""

import streamlit as st
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from components.charts import congestion_idle_heatmap

st.set_page_config(page_title="Heatmaps", page_icon="🔥", layout="wide")
st.title("🔥 Congestion & Idle Period Heatmaps")

if "filtered_df" not in st.session_state:
    st.warning("Please set filters on the main page first.")
    st.stop()

df = st.session_state["filtered_df"]

if len(df) == 0:
    st.warning("No data for the selected filters.")
    st.stop()

resolution = st.session_state.get("resolution", "hourly")

if resolution == "daily":
    st.info(
        "Day-of-week / hour-of-day heatmaps require **15-min** or **Hourly** "
        "granularity (daily data has no hour-of-day variation). "
        "Switch granularity on the main page to see the heatmap. "
        "The congested/idle window tables below still work at daily resolution."
    )
else:
    st.markdown(
        "These heatmaps show the **average Operational Load Index (OLI)** "
        "by day of week and hour of day. Darker red = more congested / "
        "over-utilized; green = idle / under-utilized."
    )
    st.plotly_chart(congestion_idle_heatmap(df, "OLI"), use_container_width=True)

st.markdown("---")
col1, col2 = st.columns(2)

# Ensure clean booleans regardless of source dtype
congested_mask = df["is_congested"].astype(bool)
idle_mask = df["is_idle"].astype(bool)

with col1:
    st.subheader("Top Congested Windows")
    congested_df = df[congested_mask]
    if len(congested_df) == 0:
        st.info("No congested intervals found for the current filters.")
    else:
        congested_summary = (
            congested_df
            .groupby(["day_name", "hour"])
            .size()
            .reset_index(name="congested_count")
            .sort_values("congested_count", ascending=False)
            .head(10)
        )
        st.dataframe(congested_summary, use_container_width=True)

with col2:
    st.subheader("Top Idle Windows")
    idle_df = df[idle_mask]
    if len(idle_df) == 0:
        st.info("No idle intervals found for the current filters.")
    else:
        idle_summary = (
            idle_df
            .groupby(["day_name", "hour"])
            .size()
            .reset_index(name="idle_count")
            .sort_values("idle_count", ascending=False)
            .head(10)
        )
        st.dataframe(idle_summary, use_container_width=True)