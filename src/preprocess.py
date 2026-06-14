"""
preprocess.py
==============
Run this ONCE (or whenever the raw CSV changes) to generate cached,
feature-engineered datasets at 15-min, hourly, and daily resolutions.
The Streamlit app reads these cached files instead of recomputing
everything on every page load.

Usage (from project root):
    python src/preprocess.py
"""

import sys
import os

sys.path.append(os.path.dirname(__file__))

from data_loader import load_and_prepare, resample_data
from features import add_all_features, add_calendar_features


RAW_PATH = "data/raw/Toronto_Island_Ferry_Tickets.csv"
PROCESSED_DIR = "data/processed"


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    print("Loading and cleaning raw data...")
    df = load_and_prepare(RAW_PATH)

    print("Engineering features (15-min resolution)...")
    df_15min = add_all_features(df)
    df_15min.to_parquet(os.path.join(PROCESSED_DIR, "ferry_15min.parquet"))
    print(f"  -> saved {len(df_15min):,} rows")

    print("Resampling to hourly resolution...")
    df_hourly = resample_data(df_15min, "h")
    df_hourly = add_calendar_features(df_hourly)
    # At hourly resolution, is_idle/is_congested were averaged across the
    # four 15-min sub-intervals (resample agg = "mean"), giving a float
    # "fraction of idle/congested sub-intervals". Threshold back to bool:
    # an hour counts as idle/congested if a majority of its sub-intervals were.
    df_hourly["is_idle"] = df_hourly["is_idle"] >= 0.5
    df_hourly["is_congested"] = df_hourly["OLI"] >= 0.75
    df_hourly.to_parquet(os.path.join(PROCESSED_DIR, "ferry_hourly.parquet"))
    print(f"  -> saved {len(df_hourly):,} rows")

    print("Resampling to daily resolution...")
    df_daily = resample_data(df_15min, "D")
    df_daily = add_calendar_features(df_daily)
    df_daily["is_idle"] = df_daily["is_idle"] >= 0.5
    df_daily["is_congested"] = df_daily["OLI"] >= 0.75
    df_daily.to_parquet(os.path.join(PROCESSED_DIR, "ferry_daily.parquet"))
    print(f"  -> saved {len(df_daily):,} rows")

    print("\nDone. Processed files written to:", PROCESSED_DIR)


if __name__ == "__main__":
    main()
