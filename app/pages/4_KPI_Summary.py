"""
Page 4: KPI Summary
"""

import streamlit as st
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from kpis import compute_all_kpis, kpis_by_group

st.set_page_config(page_title="KPI Summary", page_icon="📋", layout="wide")
st.title("📋 KPI Summary")

if "filtered_df" not in st.session_state:
    st.warning("Please set filters on the main page first.")
    st.stop()

df = st.session_state["filtered_df"]

if len(df) == 0:
    st.warning("No data for the selected filters.")
    st.stop()

st.subheader("Overall KPIs (for current filter selection)")
overall = compute_all_kpis(df)
st.json(overall)

st.markdown("---")
group_choice = st.selectbox(
    "Break down KPIs by:",
    ["season", "is_weekend", "time_band", "year", "month", "day_name"]
)

if group_choice in df.columns:
    grouped = kpis_by_group(df, group_choice)
    st.dataframe(grouped, use_container_width=True)

    csv = grouped.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download as CSV", csv,
        file_name=f"kpi_summary_by_{group_choice}.csv",
        mime="text/csv"
    )
else:
    st.warning(f"Column '{group_choice}' not available at this resolution.")

st.markdown("---")
st.subheader("KPI Definitions")
st.markdown("""
| KPI | Definition |
|---|---|
| **Capacity Utilization Ratio** | Average OLI across operating intervals. Range 0-1; higher = busier relative to the typical peak for that hour. |
| **Congestion Pressure Index (%)** | % of operating intervals where OLI >= 0.75 (over-utilized / congested). |
| **Idle Capacity Percentage (%)** | % of operating intervals that fall within a sustained low-activity run (under-utilized). |
| **Peak Strain Duration (minutes)** | Length of the longest consecutive run of congested intervals. |
| **Operational Variability Score** | Coefficient of variation (std/mean) of Total Activity Load -- higher means less predictable demand. |
""")
