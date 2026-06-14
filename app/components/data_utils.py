"""
data_utils.py
==============
Shared data-loading and filtering utilities for the Streamlit app.
Cached with st.cache_data so the parquet files are only read once per
session.
"""

import streamlit as st
import pandas as pd
import os

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed")


@st.cache_data
def load_data(resolution: str = "15min") -> pd.DataFrame:
    """
    Load a cached processed dataset.

    Parameters
    ----------
    resolution : str
        One of '15min', 'hourly', 'daily'.

    Returns
    -------
    pd.DataFrame
    """
    filenames = {
        "15min": "ferry_15min.parquet",
        "hourly": "ferry_hourly.parquet",
        "daily": "ferry_daily.parquet",
    }
    if resolution not in filenames:
        raise ValueError("resolution must be one of: 15min, hourly, daily")

    path = os.path.join(PROCESSED_DIR, filenames[resolution])
    df = pd.read_parquet(path)
    return df


def filter_data(df: pd.DataFrame, start_date, end_date,
                 seasons: list = None, only_operating: bool = True) -> pd.DataFrame:
    """
    Apply date range, season, and operating-status filters.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain 'Timestamp' and 'season' columns.
    start_date, end_date : date-like
        Inclusive date range.
    seasons : list of str, optional
        If provided, only keep rows where season is in this list.
    only_operating : bool
        If True (default), drop rows where is_operating == False.

    Returns
    -------
    pd.DataFrame
    """
    mask = (df["Timestamp"].dt.date >= start_date) & (df["Timestamp"].dt.date <= end_date)

    if seasons:
        mask &= df["season"].isin(seasons)

    if only_operating and "is_operating" in df.columns:
        mask &= df["is_operating"].astype(bool)

    return df.loc[mask].copy()
