"""
data_loader.py
================
Functions to load the raw Toronto Island Ferry ticket data, clean it,
flag operating windows, and resample it to multiple time resolutions
(15-minute, hourly, daily).

Usage:
    from src.data_loader import load_raw_data, clean_data, resample_data

    df = load_raw_data("data/raw/Toronto_Island_Ferry_Tickets.csv")
    df = clean_data(df)
    hourly = resample_data(df, "H")
    daily  = resample_data(df, "D")
"""

import pandas as pd
import numpy as np


# ---------------------------------------------------------------------
# 1. LOAD
# ---------------------------------------------------------------------
def load_raw_data(path: str) -> pd.DataFrame:
    """
    Load the raw CSV file and parse timestamps.

    Parameters
    ----------
    path : str
        Path to the raw CSV file.

    Returns
    -------
    pd.DataFrame
        Raw dataframe sorted by Timestamp, with Timestamp as a
        proper datetime column (not yet the index).
    """
    df = pd.read_csv(path)

    # Standardize column names (strip spaces, keep as-is otherwise)
    df.columns = [c.strip() for c in df.columns]

    # Parse timestamps
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])

    # Sort chronologically
    df = df.sort_values("Timestamp").reset_index(drop=True)

    return df


# ---------------------------------------------------------------------
# 2. CLEAN
# ---------------------------------------------------------------------
def clean_data(df: pd.DataFrame, spike_quantile: float = 0.995,
               rolling_window: int = 4) -> pd.DataFrame:
    """
    Clean the raw dataframe:
      - Remove exact duplicate rows
      - Validate no negative counts (drop if any slip through)
      - Flag extreme spikes (beyond `spike_quantile`) per column
      - Add smoothed (rolling median) versions of Sales/Redemption
        for visualization, while preserving raw values for KPI math
      - Add a `gap_minutes` / `is_gap` flag marking long gaps
        (ferry not operating) before the next recorded interval

    Parameters
    ----------
    df : pd.DataFrame
        Output of load_raw_data().
    spike_quantile : float
        Quantile above which a value is flagged as an extreme spike.
    rolling_window : int
        Window size (in number of rows) for rolling median smoothing.
        Default 4 = 1 hour of 15-min intervals.

    Returns
    -------
    pd.DataFrame
        Cleaned dataframe with extra columns:
        ['Sales_Smooth', 'Redemption_Smooth', 'Sales_Spike',
         'Redemption_Spike', 'gap_minutes', 'is_gap']
    """
    df = df.copy()

    # --- Remove exact duplicates ---
    df = df.drop_duplicates(subset=["Timestamp"]).reset_index(drop=True)

    # --- Validate non-negative counts ---
    df = df[(df["Sales Count"] >= 0) & (df["Redemption Count"] >= 0)]
    df = df.reset_index(drop=True)

    # --- Flag extreme spikes (kept in data, just flagged) ---
    sales_thresh = df["Sales Count"].quantile(spike_quantile)
    redemption_thresh = df["Redemption Count"].quantile(spike_quantile)

    df["Sales_Spike"] = df["Sales Count"] > sales_thresh
    df["Redemption_Spike"] = df["Redemption Count"] > redemption_thresh

    # --- Rolling median smoothing (for charts only) ---
    df["Sales_Smooth"] = (
        df["Sales Count"].rolling(window=rolling_window, min_periods=1, center=True).median()
    )
    df["Redemption_Smooth"] = (
        df["Redemption Count"].rolling(window=rolling_window, min_periods=1, center=True).median()
    )

    # --- Gap detection: how long until the next record? ---
    df["gap_minutes"] = (
        df["Timestamp"].shift(-1) - df["Timestamp"]
    ).dt.total_seconds() / 60.0

    # A "gap" means the ferry was likely not operating (threshold: > 60 min)
    df["is_gap"] = df["gap_minutes"] > 60

    return df


# ---------------------------------------------------------------------
# 3. FULL 15-MIN GRID (within operating windows only)
# ---------------------------------------------------------------------
def build_full_grid(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reindex the data onto a complete 15-minute grid spanning
    min(Timestamp) to max(Timestamp). Slots with no recorded data
    are filled with 0 and marked as non-operating via `is_operating`.

    Parameters
    ----------
    df : pd.DataFrame
        Output of clean_data().

    Returns
    -------
    pd.DataFrame
        Indexed by Timestamp on a regular 15-min grid, with columns:
        ['Sales Count', 'Redemption Count', 'is_operating']
    """
    df = df.set_index("Timestamp")[["Sales Count", "Redemption Count"]]

    full_index = pd.date_range(start=df.index.min(), end=df.index.max(), freq="15min")
    grid = df.reindex(full_index)

    # Mark which slots had real data
    grid["is_operating"] = grid["Sales Count"].notna()

    # Fill missing slots with 0 (treated as "no activity recorded")
    grid["Sales Count"] = grid["Sales Count"].fillna(0)
    grid["Redemption Count"] = grid["Redemption Count"].fillna(0)

    grid.index.name = "Timestamp"
    return grid.reset_index()


# ---------------------------------------------------------------------
# 4. RESAMPLE TO MULTIPLE RESOLUTIONS
# ---------------------------------------------------------------------
def resample_data(df: pd.DataFrame, freq: str) -> pd.DataFrame:
    """
    Resample a 15-min-indexed dataframe to a coarser resolution.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain ['Timestamp', 'Sales Count', 'Redemption Count'].
        Best used on the output of build_full_grid() or feature-engineered df.
    freq : str
        Pandas offset alias: '15min', 'h' (hourly), 'D' (daily).
        Note: use lowercase 'h' (pandas 2.2+ deprecated 'H').

    Returns
    -------
    pd.DataFrame
        Resampled dataframe with summed counts (and mean of any
        derived ratio/index columns if present).
    """
    df = df.copy().set_index("Timestamp")

    sum_cols = [c for c in ["Sales Count", "Redemption Count", "Total Activity Load"]
                 if c in df.columns]
    mean_cols = [c for c in ["Redemption Pressure Ratio", "OLI"] if c in df.columns]

    agg_dict = {c: "sum" for c in sum_cols}
    agg_dict.update({c: "mean" for c in mean_cols})

    if "is_operating" in df.columns:
        agg_dict["is_operating"] = "max"  # operating if ANY sub-interval was operating
    if "is_idle" in df.columns:
        agg_dict["is_idle"] = "mean"      # fraction of idle sub-intervals

    out = df.resample(freq).agg(agg_dict).reset_index()
    return out


# ---------------------------------------------------------------------
# 5. CONVENIENCE: ONE-CALL PIPELINE
# ---------------------------------------------------------------------
def load_and_prepare(path: str) -> pd.DataFrame:
    """
    Full pipeline: load -> clean -> build full 15-min grid.
    Does NOT add engineered features (see src/features.py for that).

    Returns
    -------
    pd.DataFrame
        15-min grid with ['Timestamp', 'Sales Count', 'Redemption Count',
        'is_operating']
    """
    df = load_raw_data(path)
    df = clean_data(df)
    grid = build_full_grid(df)
    return grid


if __name__ == "__main__":
    # Quick smoke test
    df = load_and_prepare("data/raw/Toronto_Island_Ferry_Tickets.csv")
    print(df.head())
    print(df.shape)
    print("Operating intervals:", df["is_operating"].sum())
    print("Non-operating intervals:", (~df["is_operating"]).sum())
