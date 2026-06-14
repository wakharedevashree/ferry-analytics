# Ferry Capacity Utilization & Operational Efficiency Analytics System

Operational analytics project for Toronto Island Ferry ticket data
(Jack Layton Ferry Terminal: Centre Island, Hanlan's Point, Ward's Island),
covering 2015-2025.

## Folder structure

```
ferry-analytics/
├── data/
│   ├── raw/                  # original CSV (do not edit)
│   └── processed/            # cached, feature-engineered parquet files
├── src/
│   ├── data_loader.py        # load, clean, build 15-min grid, resample
│   ├── features.py            # Total Activity Load, Redemption Pressure
│   │                           # Ratio, OLI, Idle Indicator, calendar features
│   ├── kpis.py                # all 5 KPIs + grouped KPI tables
│   └── preprocess.py          # one-time script: raw CSV -> cached parquet
├── app/
│   ├── app.py                 # Streamlit home page (filters + KPI cards)
│   ├── pages/
│   │   ├── 1_Capacity_Timeline.py
│   │   ├── 2_Heatmaps.py
│   │   ├── 3_Seasonal_Comparison.py
│   │   └── 4_KPI_Summary.py
│   └── components/
│       ├── data_utils.py      # cached data loading + filtering
│       └── charts.py          # reusable Plotly chart functions
├── notebooks/                  # EDA notebooks (for the research paper)
├── reports/                     # research paper + executive summary (markdown)
└── requirements.txt
```

## Setup

```bash
pip install -r requirements.txt
```

## Step 1: Run preprocessing (once, or whenever raw data changes)

```bash
python src/preprocess.py
```

This reads `data/raw/Toronto_Island_Ferry_Tickets.csv`, cleans it, engineers
all features (Total Activity Load, Redemption Pressure Ratio, OLI, Idle
Indicator, congestion flag, calendar features), and writes three cached
files to `data/processed/`:

- `ferry_15min.parquet`
- `ferry_hourly.parquet`
- `ferry_daily.parquet`

## Step 2: Run the dashboard

```bash
streamlit run app/app.py
```

Use the sidebar to:
- Toggle granularity (15-min / Hourly / Daily)
- Pick a date range
- Filter by season (Summer / Shoulder / Winter)
- Show only operating intervals (excludes off-season closures)

## Key definitions

| Feature | Formula |
|---|---|
| Total Activity Load | Sales Count + Redemption Count |
| Redemption Pressure Ratio | Redemption Count / (Sales Count + 1) |
| OLI (Operational Load Index) | Total Activity Load / max(Total Activity Load for that hour-of-day, historically) |
| Idle Capacity Indicator | Total Activity Load in bottom 10th percentile, sustained for 3+ consecutive intervals |
| Congestion flag | OLI >= 0.75 |

| KPI | Definition |
|---|---|
| Capacity Utilization Ratio | Mean OLI over operating intervals |
| Congestion Pressure Index (%) | % of operating intervals with OLI >= 0.75 |
| Idle Capacity Percentage (%) | % of operating intervals flagged idle |
| Peak Strain Duration (min) | Longest consecutive run of congested intervals |
| Operational Variability Score | std/mean of Total Activity Load (coefficient of variation) |

## Notes / assumptions

- The dataset does not include vessel capacity figures, so OLI is a
  **relative** load measure (normalized against historical peaks for the
  same hour-of-day), not an absolute % of physical vessel capacity.
  Document this assumption explicitly in the research paper.
- "Non-operating" intervals (long gaps in the raw data, e.g. overnight or
  off-season) are filled with 0 and flagged via `is_operating = False`.
  By default the dashboard excludes these from KPI calculations.
- Seasons: Summer = Jun-Aug, Shoulder = Apr/May/Sep/Oct, Winter = Nov-Mar.
- 2020 will show an anomalous dip (COVID-19) -- worth a dedicated callout
  in the research paper / executive summary.
