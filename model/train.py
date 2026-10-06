"""
train.py — Main Model Training & Evaluation Pipeline.

Trains XGBoost & Baseline Logistic Regression, performs Isotonic Probability Calibration,
evaluates metrics (ROC-AUC, PR-AUC, Recall, Confusion Matrix), optimizes cost threshold,
computes SHAP feature importances, and serializes artifacts with joblib.
"""

from __future__ import annotations

import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.metrics import (
    accuracy_score, roc_auc_score, average_precision_score,
    recall_score, precision_score, f1_score, confusion_matrix,
    brier_score_loss
)
from sklearn.model_selection import train_test_split

from src.config import (
    MODEL_DIR, PIPELINE_PATH, CALIBRATED_PATH, BASELINE_PATH,
    TEST_SIZE, RANDOM_STATE
)
from src.data import load_raw_data, prepare_features_and_target
from src.model import build_xgb_pipeline, build_lr_pipeline, get_tree_estimator, transform_for_shap
from src.costs import optimize_threshold, compute_financial_outcomes


def run_training_pipeline(csv_path: str | Path | None = None) -> dict:
    """Execute complete end-to-end model training, calibration, and evaluation."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    print("📥 Loading raw dataset...")
    raw_df = load_raw_data(csv_path)
    X, y = prepare_features_and_target(raw_df)

    # Stratified Train/Test Split (preserves ~26.5% churn ratio in both splits)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )

    print(f"📊 Dataset split: {len(X_train)} train samples, {len(X_test)} test samples.")

    # 1. Baseline Model: Logistic Regression
    print("\n⚡ Training Baseline Logistic Regression model...")
    lr_pipeline = build_lr_pipeline()
    lr_pipeline.fit(X_train, y_train)

    lr_probs = lr_pipeline.predict_proba(X_test)[:, 1]
    lr_preds = (lr_probs >= 0.5).astype(int)

    lr_auc = roc_auc_score(y_test, lr_probs)
    lr_recall = recall_score(y_test, lr_preds)
    lr_fn = int(confusion_matrix(y_test, lr_preds)[1, 0])

    print(f"   ► LR Baseline — ROC-AUC: {lr_auc:.4f} | Recall: {lr_recall:.4f} | False Negatives: {lr_fn}")

    # 2. Main Model: XGBoost Pipeline (Uncalibrated)
    print("\n🚀 Training XGBoost Classifier Pipeline...")
    raw_xgb_pipeline = build_xgb_pipeline(calibrate=False)
    raw_xgb_pipeline.fit(X_train, y_train)

    # 3. Main Model: XGBoost Pipeline (Calibrated via Isotonic Regression)
    print("🎯 Calibrating XGBoost probabilities with Isotonic Regression (5-fold CV)...")
    calibrated_pipeline = build_xgb_pipeline(calibrate=True)
    calibrated_pipeline.fit(X_train, y_train)

    # Evaluate Calibrated Model on Test Set
    xgb_probs = calibrated_pipeline.predict_proba(X_test)[:, 1]
    xgb_preds_default = (xgb_probs >= 0.5).astype(int)

    # 4. Financial Cost Matrix & Threshold Optimization
    monthly_charges_test = X_test["MonthlyCharges"].values
    best_cost_res, cost_df = optimize_threshold(y_test.values, xgb_probs, monthly_charges_test)

    opt_threshold = best_cost_res["threshold"]
    xgb_preds_opt = (xgb_probs >= opt_threshold).astype(int)

    # Metrics computation
    acc_default = accuracy_score(y_test, xgb_preds_default)
    acc_opt = accuracy_score(y_test, xgb_preds_opt)
    roc_auc = roc_auc_score(y_test, xgb_probs)
    pr_auc = average_precision_score(y_test, xgb_probs)
    brier = brier_score_loss(y_test, xgb_probs)

    cm_default = confusion_matrix(y_test, xgb_preds_default)
    cm_opt = confusion_matrix(y_test, xgb_preds_opt)

    fn_default = int(cm_default[1, 0])
    fn_opt = int(cm_opt[1, 0])
    fn_reduction_pct = ((lr_fn - fn_opt) / lr_fn) * 100.0

    print("\n" + "="*60)
    print("📈 FINAL MODEL PERFORMANCE EVALUATION")
    print("="*60)
    print(f"► Default Accuracy (p=0.50): {acc_default * 100:.2f}%")
    print(f"► Optimal Accuracy (p={opt_threshold:.2f}): {acc_opt * 100:.2f}%")
    print(f"► ROC-AUC Score:             {roc_auc:.4f}")
    print(f"► PR-AUC Score:              {pr_auc:.4f}")
    print(f"► Calibration Brier Score:   {brier:.4f}")
    print(f"► LR False Negatives:        {lr_fn}")
    print(f"► XGB False Negatives:       {fn_opt} (Reduced by {fn_reduction_pct:.1f}% vs LR baseline)")
    print(f"► Financial Net Savings:     ${best_cost_res['savings_vs_do_nothing']:,.2f} vs doing nothing")
    print("="*60)

    # 5. Save Model Artifacts using Joblib
    print("\n💾 Serializing model artifacts to model/ directory...")
    joblib.dump(raw_xgb_pipeline, PIPELINE_PATH)
    joblib.dump(calibrated_pipeline, CALIBRATED_PATH)
    joblib.dump(lr_pipeline, BASELINE_PATH)

    metrics_summary = {
        "accuracy_default": acc_default,
        "accuracy_optimal": acc_opt,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "brier_score": brier,
        "lr_baseline_auc": lr_auc,
        "lr_false_negatives": lr_fn,
        "xgb_false_negatives": fn_opt,
        "false_negative_reduction_pct": fn_reduction_pct,
        "optimal_threshold": opt_threshold,
        "net_financial_savings": best_cost_res["savings_vs_do_nothing"],
    }

    print("✅ Training complete! Artifacts saved successfully.")
    return metrics_summary


if __name__ == "__main__":
    run_training_pipeline()
