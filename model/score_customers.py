"""
score_customers.py — Customer Batch Scoring Engine.

Scores active customers with the calibrated XGBoost pipeline, calculates monthly
revenue at risk, and writes predictions directly into PostgreSQL (`churn_scores` table).
Falls back to CSV output if database connection is unavailable.
"""

from __future__ import annotations

import joblib
import argparse
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

from src.config import (
    CALIBRATED_PATH, DB_URI, ID_COL, TARGET, THRESHOLD_PATH
)
from src.data import load_raw_data, prepare_features_and_target
from src.costs import calculate_customer_clv


def score_active_customers(
    output_csv: str = "data/active_customer_scores.csv",
    input_csv: str | None = None,
    write_db: bool = True,
) -> pd.DataFrame:
    """Load active customers, score with calibrated model, and write to DB/CSV."""
    if not CALIBRATED_PATH.exists():
        raise FileNotFoundError(f"Calibrated model not found at '{CALIBRATED_PATH}'. Run model/train.py first.")

    print(f"Loading calibrated pipeline from {CALIBRATED_PATH}...")
    pipeline = joblib.load(CALIBRATED_PATH)

    raw_df = load_raw_data(input_csv)
    
    # Filter active customers (Churn == No) to simulate production inference
    active_mask = raw_df[TARGET].astype(str).str.strip().str.lower() == "no"
    active_df = raw_df[active_mask].copy()

    print(f"Scoring {len(active_df)} active customers...")

    X_active = active_df.drop(columns=[TARGET, ID_COL], errors="ignore")
    
    # Predict probabilities with calibrated pipeline
    churn_probs = pipeline.predict_proba(X_active)[:, 1]
    
    threshold = 0.5
    if THRESHOLD_PATH.exists():
        import json
        threshold = float(json.loads(THRESHOLD_PATH.read_text(encoding="utf-8"))["threshold"])
    churn_flags = (churn_probs >= threshold).astype(int)

    # Calculate Revenue at Risk & CLV
    monthly_charges = active_df["MonthlyCharges"].values
    # Expected one-month revenue exposure is probability-weighted.
    revenue_at_risk = churn_probs * monthly_charges
    customer_clv = calculate_customer_clv(monthly_charges)

    scored_df = pd.DataFrame({
        "customer_id": active_df[ID_COL].values,
        "tenure": active_df["tenure"].values,
        "contract": active_df["Contract"].values,
        "monthly_charges": monthly_charges,
        "churn_probability": np.round(churn_probs, 4),
        "risk_level": pd.cut(
            churn_probs,
            bins=[-0.01, 0.30, 0.60, 1.0],
            labels=["Low", "Medium", "High"]
        ),
        "is_high_risk": churn_flags,
        "revenue_at_risk": np.round(revenue_at_risk, 2),
        "clv_estimate": np.round(customer_clv, 2),
        "clv_at_risk": np.round(churn_probs * customer_clv, 2),
        "scored_at": datetime.now(timezone.utc).replace(tzinfo=None),
    })

    # Summary Stats
    total_active = len(scored_df)
    high_risk_count = int(scored_df["is_high_risk"].sum())
    total_rev_at_risk = float(scored_df["revenue_at_risk"].sum())

    print("\n" + "="*50)
    print("BATCH CUSTOMER SCORING SUMMARY")
    print("="*50)
    print(f"Total Active Customers Scored: {total_active:,}")
    share = high_risk_count / total_active if total_active else 0.0
    print(f"High Churn Risk Customers:     {high_risk_count:,} ({share:.1%})")
    print(f"Expected Monthly Revenue Exposure: ${total_rev_at_risk:,.2f}")
    print("="*50)

    # Write to PostgreSQL database table
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    scored_df.to_csv(output_path, index=False)
    print(f"Saved score export to '{output_path}'.")

    try:
        if not write_db:
            return scored_df
        engine = create_engine(DB_URI)
        insert = text("""
            INSERT INTO churn_scores (
                customer_id, tenure, contract, monthly_charges, churn_probability,
                risk_level, is_high_risk, revenue_at_risk, clv_estimate, clv_at_risk, scored_at
            ) VALUES (
                :customer_id, :tenure, :contract, :monthly_charges, :churn_probability,
                :risk_level, :is_high_risk, :revenue_at_risk, :clv_estimate, :clv_at_risk, :scored_at
            ) ON CONFLICT (customer_id) DO UPDATE SET
                tenure = EXCLUDED.tenure, contract = EXCLUDED.contract,
                monthly_charges = EXCLUDED.monthly_charges,
                churn_probability = EXCLUDED.churn_probability,
                risk_level = EXCLUDED.risk_level, is_high_risk = EXCLUDED.is_high_risk,
                revenue_at_risk = EXCLUDED.revenue_at_risk,
                clv_estimate = EXCLUDED.clv_estimate, clv_at_risk = EXCLUDED.clv_at_risk,
                scored_at = EXCLUDED.scored_at
        """)
        with engine.begin() as conn:
            conn.execute(insert, scored_df.to_dict(orient="records"))
        print("Successfully upserted scores to PostgreSQL table 'churn_scores'.")
    except Exception as e:
        print(f"PostgreSQL write skipped ({e}). The CSV export is still available at '{output_path}'.")

    return scored_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", help="Optional path to a Telco churn CSV")
    parser.add_argument("--output-csv", default="data/active_customer_scores.csv")
    parser.add_argument("--no-db", action="store_true", help="Write only the CSV score export")
    args = parser.parse_args()
    score_active_customers(args.output_csv, args.input_csv, write_db=not args.no_db)
