"""One place that builds the full analysis table (used by notebooks and the app)."""
from pathlib import Path

from src.cleaning import PROCESSED_PATH, clean_pipeline, load_processed
from src.metrics import (
    add_backlog_indicators,
    add_core_metrics,
    add_cumulative_net_intake,
    add_growth_rate,
    add_rolling_metrics,
    add_strain_relief,
)


def build_dataset(processed_path=PROCESSED_PATH):
    """Clean data plus every metric from Days 6 to 11.

    Uses the processed CSV when it exists; otherwise rebuilds it from the raw file.
    """
    if Path(processed_path).exists():
        df = load_processed(processed_path)
    else:
        df = clean_pipeline()
    df = add_core_metrics(df)
    df = add_growth_rate(df)
    df = add_cumulative_net_intake(df)
    df = add_rolling_metrics(df)
    df = add_backlog_indicators(df)
    df = add_strain_relief(df)
    return df