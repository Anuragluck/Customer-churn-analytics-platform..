"""
survival_analysis.py — Tenure Survival & Cohort Analysis.

Fits Kaplan-Meier Survival Curves by Contract Type and Cox Proportional Hazards Model
to quantify hazard ratios for churn drivers over customer lifespan.
Exports charts for Tableau & Power BI visual cohort analysis.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from lifelines import KaplanMeierFitter, CoxPHFitter
from src.config import TARGET, ID_COL, MODEL_DIR
from src.data import load_raw_data


def run_survival_analysis(output_dir: str | Path | None = None) -> dict:
    """Perform Kaplan-Meier and Cox Proportional Hazards survival analysis."""
    save_dir = Path(output_dir) if output_dir else MODEL_DIR
    save_dir.mkdir(parents=True, exist_ok=True)

    print("Loading raw data for survival analysis...")
    df = load_raw_data()

    # Tenure = time event variable; Churn = binary event (1 = churned, 0 = censored)
    T = df["tenure"]
    E = (df[TARGET].astype(str).str.strip().str.lower() == "yes").astype(int)

    # 1. Kaplan-Meier Overall Curve
    kmf = KaplanMeierFitter()
    kmf.fit(T, event_observed=E, label="All Customers")

    fig, ax = plt.subplots(figsize=(10, 6))
    kmf.plot_survival_function(ax=ax, ci_show=True, color="#1f77b4", linewidth=2.5)

    # 2. Kaplan-Meier Stratified by Contract Type
    fig_contract, ax_contract = plt.subplots(figsize=(10, 6))
    contracts = df["Contract"].unique()
    colors = {"Month-to-month": "#e377c2", "One year": "#2ca02c", "Two year": "#1f77b4"}

    median_survivals = {}
    for contract_type in contracts:
        mask = df["Contract"] == contract_type
        kmf_contract = KaplanMeierFitter()
        kmf_contract.fit(T[mask], event_observed=E[mask], label=f"Contract: {contract_type}")
        kmf_contract.plot_survival_function(
            ax=ax_contract, ci_show=False, color=colors.get(contract_type, None), linewidth=2.5
        )
        median_survivals[contract_type] = kmf_contract.median_survival_time_

    ax_contract.set_title("Customer Survival Probability by Contract Type (Kaplan-Meier)", fontsize=14, fontweight="bold")
    ax_contract.set_xlabel("Tenure (Months)", fontsize=12)
    ax_contract.set_ylabel("Survival Probability (Retention Rate)", fontsize=12)
    ax_contract.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()

    km_chart_path = save_dir / "survival_by_contract.png"
    fig_contract.savefig(km_chart_path, dpi=300)
    plt.close(fig_contract)
    plt.close(fig)

    print(f"Saved Kaplan-Meier plot to {km_chart_path}")
    print("\nMedian Survival Times (Months to 50% Churn):")
    for contract, median in median_survivals.items():
        print(f"   {contract}: {median} months")

    # 3. Cox Proportional Hazards Model
    print("\nFitting Cox Proportional Hazards Model...")
    # Tenure is required as the duration column; lifelines removes it from the
    # covariates when duration_col is specified below.
    cox_cols = ["tenure", "MonthlyCharges", "Contract", "InternetService", TARGET]
    cox_df = df[cox_cols].copy()
    cox_df[TARGET] = (cox_df[TARGET].astype(str).str.strip().str.lower() == "yes").astype(int)

    # Convert categorical to dummies for Cox model
    cox_df = pd.get_dummies(cox_df, columns=["Contract", "InternetService"], drop_first=True)

    cph = CoxPHFitter()
    cph.fit(cox_df, duration_col="tenure", event_col=TARGET, robust=True)

    hazard_ratios = cph.hazard_ratios_.to_dict()

    print("\nHazard Ratios (Risk Multipliers):")
    for feature, hr in hazard_ratios.items():
        print(f"   {feature}: {hr:.4f}")

    return {
        "median_survivals": median_survivals,
        "hazard_ratios": hazard_ratios,
        "km_plot_path": str(km_chart_path),
    }


if __name__ == "__main__":
    run_survival_analysis()
