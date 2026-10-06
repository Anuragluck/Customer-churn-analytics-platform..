"""
costs.py — Business Cost Model & Decision Threshold Optimizer.

Transforms ML probabilities into financial dollars and cents.
Sweeps classification thresholds from 0.05 to 0.95 to maximize Net Financial Savings.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from src.config import (
    RETENTION_OFFER_COST, RETENTION_SUCCESS_RATE, AVG_CUSTOMER_LIFETIME_MONTHS
)


def calculate_customer_clv(
    monthly_charges: float | np.ndarray,
    remaining_months: float = AVG_CUSTOMER_LIFETIME_MONTHS
) -> float | np.ndarray:
    """Estimate Customer Lifetime Value (CLV) based on monthly bill & remaining tenure."""
    return monthly_charges * remaining_months


def compute_financial_outcomes(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    monthly_charges: np.ndarray,
    threshold: float,
    retention_cost: float = RETENTION_OFFER_COST,
    success_rate: float = RETENTION_SUCCESS_RATE
) -> dict[str, float]:
    """
    Compute total financial balance sheet for a given decision threshold.
    
    Logic:
    - Target = 1 (Actual Churner):
      - If predicted Churn (TP): Send offer ($ cost). With success_rate %, save customer CLV.
      - If predicted Stay (FN): Customer leaves. Lose 100% of customer CLV.
    - Target = 0 (Actual Retained):
      - If predicted Churn (FP): Send offer ($ cost). Customer stays anyway (wasted offer).
      - If predicted Stay (TN): Do nothing ($0 cost, full revenue retained).
    """
    y_pred = (y_prob >= threshold).astype(int)

    tp = (y_pred == 1) & (y_true == 1)
    fp = (y_pred == 1) & (y_true == 0)
    fn = (y_pred == 0) & (y_true == 1)
    tn = (y_pred == 0) & (y_true == 0)

    customer_clv = calculate_customer_clv(monthly_charges)

    # Costs
    cost_tp_offers = np.sum(tp) * retention_cost
    cost_fp_offers = np.sum(fp) * retention_cost
    total_outreach_cost = cost_tp_offers + cost_fp_offers

    # Saved Revenue (TPs who accept the offer)
    saved_revenue = np.sum(customer_clv[tp]) * success_rate

    # Unavoidable Revenue Loss (FNs who leave without intervention + unpersuaded TPs)
    lost_revenue_fn = np.sum(customer_clv[fn])
    lost_revenue_tp_failed = np.sum(customer_clv[tp]) * (1.0 - success_rate)
    total_revenue_lost = lost_revenue_fn + lost_revenue_tp_failed

    # Net Financial Value (Saved Revenue - Total Outreach Cost)
    net_value = saved_revenue - total_outreach_cost

    return {
        "threshold": threshold,
        "tp_count": int(np.sum(tp)),
        "fp_count": int(np.sum(fp)),
        "fn_count": int(np.sum(fn)),
        "tn_count": int(np.sum(tn)),
        "outreach_cost": float(total_outreach_cost),
        "saved_revenue": float(saved_revenue),
        "lost_revenue": float(total_revenue_lost),
        "net_value": float(net_value),
    }


def optimize_threshold(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    monthly_charges: np.ndarray,
    step: float = 0.01
) -> dict[str, float]:
    """
    Sweep thresholds from 0.05 to 0.95 to find the threshold that maximizes Net Savings.
    Also computes baseline comparisons (Do Nothing vs Contact Everyone).
    """
    thresholds = np.arange(0.05, 0.95 + step, step)
    results = []

    for t in thresholds:
        res = compute_financial_outcomes(y_true, y_prob, monthly_charges, threshold=round(float(t), 2))
        results.append(res)

    df_res = pd.DataFrame(results)

    # Baseline 1: Do Nothing (threshold = 1.0) -> $0 outreach cost, $0 saved revenue
    do_nothing = compute_financial_outcomes(y_true, y_prob, monthly_charges, threshold=1.0)

    # Baseline 2: Contact Everyone (threshold = 0.0) -> max outreach cost
    contact_all = compute_financial_outcomes(y_true, y_prob, monthly_charges, threshold=0.0)

    # Find optimal threshold
    best_idx = df_res["net_value"].idxmax()
    best_row = df_res.loc[best_idx].to_dict()

    best_row["savings_vs_do_nothing"] = float(best_row["net_value"] - do_nothing["net_value"])
    best_row["savings_vs_contact_all"] = float(best_row["net_value"] - contact_all["net_value"])

    return best_row, df_res
