"""Cleaning pipeline for the UAC care system dataset.

Raw CSV  ->  tidy, validated, complete daily table.
Run from the project root:  python -m src.cleaning
"""
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "HHS_Unaccompanied_Alien_Children_Program.csv"
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed" / "uac_daily_clean.csv"

COLUMN_NAMES = [
    "date",
    "apprehended",
    "cbp_custody",
    "cbp_transferred",
    "hhs_care",
    "hhs_discharged",
]
NUMERIC_COLS = COLUMN_NAMES[1:]


def load_raw(path=RAW_PATH):
    """Read the raw CSV exactly as it is."""
    return pd.read_csv(path)


def rename_columns(df):
    """Replace the long original column names with short snake_case names."""
    if len(df.columns) != len(COLUMN_NAMES):
        raise ValueError(
            f"Expected {len(COLUMN_NAMES)} columns, found {len(df.columns)}"
        )
    df = df.copy()
    df.columns = COLUMN_NAMES
    return df


def drop_empty_rows(df):
    """Remove rows where every column is empty."""
    return df.dropna(how="all").copy()


def convert_types(df):
    """Real dates, and whole-number counts (commas removed)."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], format="%B %d, %Y")
    for col in NUMERIC_COLS:
        cleaned = df[col].astype(str).str.replace(",", "", regex=False)
        df[col] = pd.to_numeric(cleaned).astype("Int64")
    return df


def sort_and_check(df):
    """Oldest first, and stop if any date appears twice."""
    df = df.sort_values("date").reset_index(drop=True)
    if df["date"].duplicated().any():
        raise ValueError("Duplicate dates found in the data")
    return df


def build_daily_index(df):
    """One row per calendar day. Unreported days stay empty and are flagged."""
    full_range = pd.date_range(df["date"].min(), df["date"].max(), freq="D")
    daily = df.set_index("date").reindex(full_range)
    daily.index.name = "date"
    daily["is_reported"] = daily["hhs_care"].notna()
    return daily


def add_validation_flags(df):
    """True/False flags for the rules from Day 4 (no rows are removed)."""
    df = df.copy()
    df["flag_transfer_gt_custody"] = (
        (df["cbp_transferred"] > df["cbp_custody"]).fillna(False).astype(bool)
    )
    df["flag_discharge_gt_hhs"] = (
        (df["hhs_discharged"] > df["hhs_care"]).fillna(False).astype(bool)
    )
    return df


def clean_pipeline(raw_path=RAW_PATH):
    """Run every step in order and return the processed table."""
    df = load_raw(raw_path)
    df = rename_columns(df)
    df = drop_empty_rows(df)
    df = convert_types(df)
    df = sort_and_check(df)
    df = build_daily_index(df)
    df = add_validation_flags(df)
    return df


def save_processed(df, path=PROCESSED_PATH):
    """Write the processed table to CSV (the date index becomes a column)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path)
    return path


def load_processed(path=PROCESSED_PATH):
    """Read the processed CSV back with the right types."""
    df = pd.read_csv(path, parse_dates=["date"], index_col="date")
    df[NUMERIC_COLS] = df[NUMERIC_COLS].astype("Int64")
    return df


if __name__ == "__main__":
    result = clean_pipeline()
    out = save_processed(result)
    print(f"Saved {len(result)} rows to {out}")
    print(f"Reported days: {int(result['is_reported'].sum())}")