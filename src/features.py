"""
features.py
=============
Feature engineering for the Ferry Capacity Utilization & Operational
Efficiency Analytics System.

Adds:
    - Total Activity Load
    - Redemption Pressure Ratio
    - Operational Load Index (OLI)
    - Idle Capacity Indicator
    - Calendar features (hour, day_of_week, is_weekend, month, season, year, time_band)

Usage:
    from src.features import add_all_features

    df = add_all_features(df)
"""

import pandas as pd
import numpy as np


# ---------------------------------------------------------------------
# CALENDAR FEATURES
# ---------------------------------------------------------------------
def add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add calendar-based columns derived from the Timestamp column.

    Adds
    ----
    year, month, hour, day_of_week (Mon=0..Sun=6), day_name,
    is_weekend (bool), season (Summer/Shoulder/Winter),
    time_band (Morning/Afternoon/Evening/Night)
    """
    df = df.copy()
    ts = df["Timestamp"]

    df["year"] = ts.dt.year
    df["month"] = ts.dt.month
    df["hour"] = ts.dt.hour
    df["day_of_week"] = ts.dt.dayofweek
    df["day_name"] = ts.dt.day_name()
    df["is_weekend"] = df["day_of_week"].isin([5, 6])

    # Seasonal grouping tailored to Toronto Island Ferry operations:
    #   Summer (peak):     June, July, August
    #   Shoulder:          April, May, September, October
    #   Winter (off-season): November - March
    def _season(month: int) -> str:
        if month in (6, 7, 8):
            return "Summer"
        elif month in (4, 5, 9, 10):
            return "Shoulder"
        else:
            return "Winter"

    df["season"] = df["month"].apply(_season)

    # Time-of-day band
    def _time_band(hour: int) -> str:
        if 5 <= hour < 12:
            return "Morning"
        elif 12 <= hour < 17:
            return "Afternoon"
        elif 17 <= hour < 21:
            return "Evening"
        else:
            return "Night"

    df["time_band"] = df["hour"].apply(_time_band)

    return df


# ---------------------------------------------------------------------
# CORE CAPACITY FEATURES
# ---------------------------------------------------------------------
def add_activity_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add Total Activity Load and Redemption Pressure Ratio.

    Total Activity Load = Sales Count + Redemption Count
    Redemption Pressure Ratio = Redemption Count / (Sales Count + 1)
    """
    df = df.copy()
    df["Total Activity Load"] = df["Sales Count"] + df["Redemption Count"]
    df["Redemption Pressure Ratio"] = df["Redemption Count"] / (df["Sales Count"] + 1)
    return df


def add_oli(df: pd.DataFrame, method: str = "hour_of_day") -> pd.DataFrame:
    """
    Add the Operational Load Index (OLI): a normalized 0-1+ measure of
    how busy a given 15-min interval is, relative to a baseline.

    Parameters
    ----------
    df : pd.DataFrame
        Must already contain 'Total Activity Load' and 'hour' columns
        (run add_activity_features and add_calendar_features first).
    method : str
        'hour_of_day'  -> normalize against the max Total Activity Load
                          observed historically for that hour of day
                          (captures "is this hour busier than usual for
                          this time of day?"). Range ~ [0, 1].
        'zscore'       -> standard z-score of Total Activity Load across
                          the whole dataset (can be negative).

    Returns
    -------
    pd.DataFrame
        With added 'OLI' column.
    """
    df = df.copy()

    if method == "hour_of_day":
        hourly_max = df.groupby("hour")["Total Activity Load"].max().replace(0, 1)
        df["OLI"] = df["Total Activity Load"] / df["hour"].map(hourly_max)
    elif method == "zscore":
        mean = df["Total Activity Load"].mean()
        std = df["Total Activity Load"].std()
        df["OLI"] = (df["Total Activity Load"] - mean) / (std if std > 0 else 1)
    else:
        raise ValueError("method must be 'hour_of_day' or 'zscore'")

    return df


def add_idle_indicator(df: pd.DataFrame, idle_quantile: float = 0.10,
                        min_consecutive: int = 3) -> pd.DataFrame:
    """
    Flag intervals as "idle" if Total Activity Load is at or below the
    `idle_quantile` threshold AND the interval is part of a sustained
    run of >= `min_consecutive` such low-activity intervals while the
    ferry is operating.

    Adds
    ----
    is_low_activity : bool   -- below the idle threshold
    is_idle          : bool  -- part of a sustained idle run (the
                                 official Idle Capacity Indicator)
    idle_run_length  : int   -- length of the consecutive idle run
                                 this row belongs to (0 if not idle)
    """
    df = df.copy()

    # Only consider operating intervals for the threshold calc
    if "is_operating" in df.columns:
        operating_mask = df["is_operating"]
    else:
        operating_mask = pd.Series(True, index=df.index)

    threshold = df.loc[operating_mask, "Total Activity Load"].quantile(idle_quantile)

    df["is_low_activity"] = (df["Total Activity Load"] <= threshold) & operating_mask

    # Identify consecutive runs of is_low_activity
    run_id = (df["is_low_activity"] != df["is_low_activity"].shift()).cumsum()
    run_lengths = df.groupby(run_id)["is_low_activity"].transform("size")

    df["idle_run_length"] = np.where(df["is_low_activity"], run_lengths, 0)
    df["is_idle"] = df["is_low_activity"] & (df["idle_run_length"] >= min_consecutive)

    return df


# ---------------------------------------------------------------------
# CONGESTION FLAG (used by KPIs / heatmaps)
# ---------------------------------------------------------------------
def add_congestion_indicator(df: pd.DataFrame, oli_threshold: float = 0.75) -> pd.DataFrame:
    """
    Flag intervals as congested when OLI exceeds `oli_threshold`.
    Requires 'OLI' column (run add_oli first).

    Adds
    ----
    is_congested : bool
    """
    df = df.copy()
    df["is_congested"] = df["OLI"] >= oli_threshold
    return df


# ---------------------------------------------------------------------
# ONE-CALL PIPELINE
# ---------------------------------------------------------------------
def add_all_features(df: pd.DataFrame,
                      oli_method: str = "hour_of_day",
                      idle_quantile: float = 0.10,
                      min_consecutive_idle: int = 3,
                      oli_congestion_threshold: float = 0.75) -> pd.DataFrame:
    """
    Run the full feature engineering pipeline in the correct order.

    Parameters
    ----------
    df : pd.DataFrame
        Output of data_loader.load_and_prepare() -- must contain
        ['Timestamp', 'Sales Count', 'Redemption Count', 'is_operating'].

    Returns
    -------
    pd.DataFrame
        Fully featured dataframe ready for KPI calculation, EDA, and
        the Streamlit dashboard.
    """
    df = add_calendar_features(df)
    df = add_activity_features(df)
    df = add_oli(df, method=oli_method)
    df = add_idle_indicator(df, idle_quantile=idle_quantile,
                             min_consecutive=min_consecutive_idle)
    df = add_congestion_indicator(df, oli_threshold=oli_congestion_threshold)
    return df


if __name__ == "__main__":
    from data_loader import load_and_prepare

    df = load_and_prepare("data/raw/Toronto_Island_Ferry_Tickets.csv")
    df = add_all_features(df)

    print(df.head())
    print(df[["Total Activity Load", "Redemption Pressure Ratio", "OLI",
              "is_idle", "is_congested", "season", "time_band"]].describe(include="all"))
