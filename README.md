# UAC Care System Analytics

A healthcare capacity analytics framework for monitoring the care system
for Unaccompanied Alien Children (UAC) across CBP and HHS, built as part of
an internship project with Unified Mentor.

## Problem
Daily operational data exists, but there is no centralized framework to assess
total care load, inflow vs outflow balance, capacity stress and relief periods,
and long-term sustainability of care delivery.

## Objectives
- Quantify daily and cumulative care load across CBP and HHS
- Identify periods of capacity strain and relief
- Analyze the balance between intake, transfers, and discharges

## Dataset
Daily reporting from **12 Jan 2023 to 21 Dec 2025**.

| Original column | Clean name | Meaning |
|---|---|---|
| Date | `date` | Reporting date |
| Children apprehended and placed in CBP custody | `apprehended` | Daily intake |
| Children in CBP custody | `cbp_custody` | Active CBP care load |
| Children transferred out of CBP custody | `cbp_transferred` | Flow into HHS |
| Children in HHS Care | `hhs_care` | Active HHS care load |
| Children discharged from HHS Care | `hhs_discharged` | Sponsor placements |

### Initial data findings (Day 2)
- The file has 1,170 rows, but only **720 contain data**. The other 450 are empty.
- `Children in HHS Care` is stored as text (e.g. "2,484") because of thousands separators.
- Rows are ordered newest first, so they must be sorted for time-series work.
- Reporting is not daily: **355 of 1,075 calendar days are missing**, and Fridays and Saturdays are almost never reported.
- **86 rows** have transfers greater than CBP custody. These are flagged for review, not deleted.
- Discharges never exceed HHS care.

## Planned Deliverables
- [ ] Cleaned and validated dataset
- [ ] Derived capacity metrics and KPIs
- [ ] Streamlit dashboard
- [ ] Research paper
- [ ] Executive summary

## Project Structure
- `data/raw/` original data (never modified)
- `data/processed/` cleaned data
- `notebooks/` exploration and EDA
- `src/` reusable analysis code
- `app/` Streamlit dashboard
- `reports/` paper and executive summary
- `tests/` unit tests

## Setup
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

The raw CSV is not included in the repository. Place it in `data/raw/`
before running the notebooks.

## Progress Log
- **Day 1:** Repository setup, folder structure, virtual environment, README
- **Day 2:** Loaded the dataset, inspected structure and data types, renamed columns, removed empty rows, found data quality issues (`notebooks/01_data_loading.ipynb`)
-- **Day 3:** Converted dates, sorted chronologically, found no duplicates, built a complete 1,075-day index and flagged 355 unreported days (`notebooks/02_time_index.ipynb`)

- **Day 4:** Defined validation rules (R1 to R4), flagged 106 anomalies across 104 dates, and checked how well transfers minus discharges explains HHS care changes (`notebooks/03_validation.ipynb`, `data/processed/anomaly_report.csv`)

- **Day 5:** Built a reusable cleaning pipeline (`src/cleaning.py`) that produces a validated 1,075-day table (`data/processed/uac_daily_clean.csv`), verified against earlier results (`notebooks/04_check_clean_data.ipynb`)

- **Day 6:** Built core metrics (`src/metrics.py`): Total System Load and Net Daily Intake, with unit tests. Found that Net Daily Intake does not fully explain actual HHS care changes in 2023 and 2024 (`notebooks/05_core_metrics.ipynb`)