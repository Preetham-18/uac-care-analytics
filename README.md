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
    python -m venv venv
    source venv/bin/activate      # Windows: venv\Scripts\activate
    pip install -r requirements.txt

## Progress Log
- Day 1: Repository setup and project structure
