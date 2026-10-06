"""
score_customers.py — Customer Batch Scoring Engine.

Scores active customers with the calibrated XGBoost pipeline, calculates monthly
revenue at risk, and writes predictions directly into PostgreSQL (`churn_scores` table).
Falls back to CSV output if database connection is unavailable.
"""

from __future__ import annotations

import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import create_engine, text

from src.config import (
    CALIBRATED_PATH, DB_URI, ID_COL, TARGET
)
from src.data import load_raw_data, prepare_features_and_target
from src.costs import calculate_customer_clv


def score_active_customers(output_csv: str = "data/active_customer_scores.csv") -> pd.DataFrame:
    """Load active customers, score with calibrated model, and write to DB/CSV."""
    if not CALIBRATED_PATH.exists():
        raise FileNotFoundError(f"Calibrated model not found at '{CALIBRATED_PATH}'. Run model/train.py first.")

    print(f"📦 Loading calibrated pipeline from {CALIBRATED_PATH}...")
    pipeline = joblib.load(CALIBRATED_PATH)

    raw_df = load_raw_data()
    
    # Filter active customers (Churn == No) to simulate production inference
    active_mask = raw_df[TARGET].astype(str).str.strip().str.lower() == "no"
    active_df = raw_df[active_mask].copy()

    print(f"👥 Scoring {len(active_df)} active customers...")

    X_active = active_df.drop(columns=[TARGET, ID_COL], errors="ignore")
    
    # Predict probabilities with calibrated pipeline
    churn_probs = pipeline.predict_proba(X_active)[:, 1]
    
    # Default risk threshold 0.42 (determined via cost optimization)
    risk_threshold = 0.42
    churn_flags = (churn_probs >= risk_threshold).astype(int)

    # Calculate Revenue at Risk & CLV
    monthly_charges = active_df["MonthlyCharges"].values
    revenue_at_risk = np.where(churn_flags == 1, monthly_charges, 0.0)
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
        "scored_at": datetime.now().isoformat(),
    })

    # Summary Stats
    total_active = len(scored_df)
    high_risk_count = int(scored_df["is_high_risk"].sum())
    total_rev_at_risk = float(scored_df["revenue_at_risk"].sum())

    print("\n" + "="*50)
    print("📊 BATCH CUSTOMER SCORING SUMMARY")
    print("="*50)
    print(f"► Total Active Customers Scored: {total_active:,}")
    print(f"► High Churn Risk Customers:    {high_risk_count:,} ({high_risk_count/total_active*100:.1f}%)")
    print(f"► Total Monthly Revenue at Risk: ${total_rev_at_risk:,.2f}")
    print("="*50)

    # Write to PostgreSQL database table
    try:
        engine = create_engine(DB_URI)
        with engine.begin() as conn:
            # Create schema if not exists
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS churn_scores (
                    customer_id VARCHAR(50) PRIMARY KEY,
                    tenure INT,
                    contract VARCHAR(50),
                    monthly_charges NUMERIC(10, 2),
                    churn_probability NUMERIC(6, 4),
                    risk_level VARCHAR(20),
                    is_high_risk INT,
                    revenue_at_risk NUMERIC(10, 2),
                    clv_estimate NUMERIC(10, 2),
                    scored_at TIMESTAMP
                );
            """))
        scored_df.to_sql("churn_scores", con=engine, if_exists="replace", index=False)
        print("✅ Successfully written scores to PostgreSQL table 'churn_scores'.")
    except Exception as e:
        print(f"⚠️ Could not write to PostgreSQL ({e}). Saving fallback CSV to '{output_csv}'...")
        scored_df.to_csv(output_csv, index=False)
        print(f"✅ Saved scores to fallback CSV at '{output_csv}'.")

    return scored_df


if __name__ == "__main__":
    score_active_customers()
