"""
data.py — Data loading, cleaning, and feature engineering.

Preserves pandas DataFrame structure throughout so that sklearn FunctionTransformer
and ColumnTransformer work seamlessly without column-name loss.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from pathlib import Path
from src.config import (
    RAW_CSV, ID_COL, TARGET, BINARY_COLS, MULTI_COLS,
    RAW_NUMERIC, SERVICE_COLS
)


def load_raw_data(csv_path: str | Path | None = None) -> pd.DataFrame:
    """Load raw Telco Customer Churn CSV and clean basic data types."""
    path = Path(csv_path) if csv_path else RAW_CSV
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found at '{path}'. Please download telco_churn.csv into data/ directory."
        )

    df = pd.read_csv(path)

    # Convert TotalCharges to numeric (handles empty spaces ' ' in raw Kaggle CSV)
    if "TotalCharges" in df.columns:
        df["TotalCharges"] = pd.to_numeric(df["TotalCharges"].astype(str).str.strip(), errors="coerce")
        # Impute missing TotalCharges with MonthlyCharges * tenure (or 0 if tenure=0)
        mask = df["TotalCharges"].isna()
        df.loc[mask, "TotalCharges"] = df.loc[mask, "MonthlyCharges"] * df.loc[mask, "tenure"]

    # SeniorCitizen is integer (0/1) in raw CSV — convert to string Yes/No for consistent categorical handling
    if "SeniorCitizen" in df.columns and df["SeniorCitizen"].dtype != object:
        df["SeniorCitizen"] = df["SeniorCitizen"].map({1: "Yes", 0: "No"}).fillna("No")

    return df


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Feature engineering transformer for sklearn Pipeline.
    
    Accepts a pandas DataFrame and returns a new pandas DataFrame with
    engineered numerical & categorical features appended.
    Must return a DataFrame to preserve column names for ColumnTransformer.
    """
    X = df.copy()

    # 1. tenure_months_ratio: progress along standard 72-month contract lifespan
    if "tenure" in X.columns:
        X["tenure_months_ratio"] = (X["tenure"] / 72.0).clip(0.0, 1.0)

    # 2. charge_per_tenure: monthly charge relative to tenure duration
    if "MonthlyCharges" in X.columns and "tenure" in X.columns:
        X["charge_per_tenure"] = X["MonthlyCharges"] / (X["tenure"] + 1.0)

    # 3. total_services: count of active subscribed add-on services
    active_service_count = np.zeros(len(X))
    for col in SERVICE_COLS:
        if col in X.columns:
            active_service_count += (X[col] == "Yes").astype(int)
    X["total_services"] = active_service_count

    # 4. overpay_ratio: ratio of cumulative monthly bills to recorded TotalCharges
    if "MonthlyCharges" in X.columns and "tenure" in X.columns and "TotalCharges" in X.columns:
        expected_total = X["MonthlyCharges"] * X["tenure"]
        X["overpay_ratio"] = expected_total / (X["TotalCharges"] + 1.0)

    # 5. has_internet_bundle: binary indicator for fiber/DSL + at least 2 add-ons
    if "InternetService" in X.columns:
        has_internet = (X["InternetService"].isin(["DSL", "Fiber optic"])).astype(int)
        X["has_internet_bundle"] = ((has_internet == 1) & (X["total_services"] >= 2)).astype(int)

    return X


def prepare_features_and_target(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Separate features X and binary target y (1 = Churn, 0 = Retained)."""
    df_clean = load_raw_data() if df is None else df.copy()

    y = (df_clean[TARGET].astype(str).str.strip().str.lower() == "yes").astype(int)
    X = df_clean.drop(columns=[TARGET, ID_COL], errors="ignore")

    return X, y
