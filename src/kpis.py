"""
kpis.py
========
Key Performance Indicator (KPI) calculations for the Ferry Capacity
Utilization & Operational Efficiency Analytics System.

KPIs implemented
-----------------
1. Capacity Utilization Ratio   -- average OLI (0-1 scale) over a period
2. Congestion Pressure Index    -- % of operating intervals flagged congested
3. Idle Capacity Percentage     -- % of operating intervals flagged idle
4. Peak Strain Duration          -- longest consecutive run of congested intervals
5. Operational Variability Score -- coefficient of variation of Total Activity Load

Usage:
    from src.kpis import compute_all_kpis, kpis_by_group

    overall = compute_all_kpis(df)
    by_season = kpis_by_group(df, "season")
"""

import pandas as pd
import numpy as np


# ---------------------------------------------------------------------
# INDIVIDUAL KPI FUNCTIONS
# ---------------------------------------------------------------------
def capacity_utilization_ratio(df: pd.DataFrame) -> float:
    """
    Average Operational Load Index (OLI) across operating intervals.
    Interpreted as: on average, what fraction of "typical peak load
    for that hour" is being used? Range ~ [0, 1].
    """
    op = df[df["is_operating"]] if "is_operating" in df.columns else df
    if len(op) == 0:
        return np.nan
    return op["OLI"].mean()


def congestion_pressure_index(df: pd.DataFrame) -> float:
    """
    Percentage of operating intervals flagged as congested
    (is_congested == True). Range [0, 100].
    """
    op = df[df["is_operating"]] if "is_operating" in df.columns else df
    if len(op) == 0:
        return np.nan
    return 100 * op["is_congested"].mean()


def idle_capacity_percentage(df: pd.DataFrame) -> float:
    """
    Percentage of operating intervals flagged as idle
    (is_idle == True, i.e. sustained low-activity periods). Range [0, 100].
    """
    op = df[df["is_operating"]] if "is_operating" in df.columns else df
    if len(op) == 0:
        return np.nan
    return 100 * op["is_idle"].mean()


def peak_strain_duration(df: pd.DataFrame, interval_minutes: int = 15) -> float:
    """
    Length (in minutes) of the longest consecutive run of congested
    intervals (is_congested == True) within the given dataframe.

    Note: assumes df is already sorted by Timestamp and at a fixed
    interval resolution (default 15 min).
    """
    if "is_congested" not in df.columns or len(df) == 0:
        return 0.0

    flags = df["is_congested"].values
    max_run = 0
    current_run = 0
    for f in flags:
        if f:
            current_run += 1
            max_run = max(max_run, current_run)
        else:
            current_run = 0

    return max_run * interval_minutes


def operational_variability_score(df: pd.DataFrame) -> float:
    """
    Coefficient of variation (std / mean) of Total Activity Load.
    Higher values = more unstable / unpredictable utilization patterns.
    Returns np.nan if mean is 0.
    """
    op = df[df["is_operating"]] if "is_operating" in df.columns else df
    if len(op) == 0:
        return np.nan
    mean = op["Total Activity Load"].mean()
    std = op["Total Activity Load"].std()
    if mean == 0:
        return np.nan
    return std / mean


# ---------------------------------------------------------------------
# AGGREGATE: ALL KPIs FOR A GIVEN SLICE
# ---------------------------------------------------------------------
def compute_all_kpis(df: pd.DataFrame, interval_minutes: int = 15) -> dict:
    """
    Compute all five KPIs for the given dataframe slice.

    Returns
    -------
    dict with keys:
        'Capacity Utilization Ratio'
        'Congestion Pressure Index (%)'
        'Idle Capacity Percentage (%)'
        'Peak Strain Duration (minutes)'
        'Operational Variability Score'
    """
    return {
        "Capacity Utilization Ratio": round(capacity_utilization_ratio(df), 4),
        "Congestion Pressure Index (%)": round(congestion_pressure_index(df), 2),
        "Idle Capacity Percentage (%)": round(idle_capacity_percentage(df), 2),
        "Peak Strain Duration (minutes)": peak_strain_duration(df, interval_minutes),
        "Operational Variability Score": round(operational_variability_score(df), 4),
    }


# ---------------------------------------------------------------------
# GROUPED KPIs (e.g. by season, year, weekday/weekend, time_band)
# ---------------------------------------------------------------------
def kpis_by_group(df: pd.DataFrame, group_col: str,
                  interval_minutes: int = 15) -> pd.DataFrame:
    """
    Compute all KPIs separately for each value of `group_col`.

    Parameters
    ----------
    df : pd.DataFrame
        Fully featured dataframe (output of add_all_features).
    group_col : str
        Column to group by, e.g. 'season', 'year', 'is_weekend', 'time_band'.

    Returns
    -------
    pd.DataFrame
        One row per group value, one column per KPI.
    """
    results = {}
    for group_value, sub_df in df.groupby(group_col):
        results[group_value] = compute_all_kpis(sub_df, interval_minutes)

    return pd.DataFrame(results).T.rename_axis(group_col).reset_index()


if __name__ == "__main__":
    import sys
    sys.path.append(".")
    from data_loader import load_and_prepare
    from features import add_all_features

    df = load_and_prepare("data/raw/Toronto_Island_Ferry_Tickets.csv")
    df = add_all_features(df)

    print("=== Overall KPIs ===")
    for k, v in compute_all_kpis(df).items():
        print(f"{k}: {v}")

    print("\n=== KPIs by Season ===")
    print(kpis_by_group(df, "season"))

    print("\n=== KPIs by Weekend/Weekday ===")
    print(kpis_by_group(df, "is_weekend"))

    print("\n=== KPIs by Year ===")
    print(kpis_by_group(df, "year"))
