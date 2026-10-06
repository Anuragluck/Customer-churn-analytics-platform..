"""Train, evaluate, and serialize the churn prediction workflow.

The test set is held out until final evaluation. The cost-based operating
threshold is selected on a separate validation split and then saved with the
model so scoring and the Streamlit app use the same policy.
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, average_precision_score, brier_score_loss,
    confusion_matrix, precision_score, recall_score, roc_auc_score,
)
from sklearn.model_selection import train_test_split

from src.config import (
    BASELINE_PATH, CALIBRATED_PATH, MODEL_DIR, METRICS_PATH, RANDOM_STATE,
    TEST_SIZE, THRESHOLD_PATH,
)
from src.costs import compute_financial_outcomes, optimize_threshold
from src.data import load_raw_data, prepare_features_and_target
from src.model import build_lr_pipeline, build_xgb_pipeline, get_tree_estimator, transform_for_shap
from src.config import XGBOOST_PARAMS


def _evaluate(y_true: pd.Series, probabilities: np.ndarray, threshold: float) -> dict:
    predictions = (probabilities >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, predictions, labels=[0, 1]).ravel()
    return {
        "threshold": float(threshold),
        "accuracy": float(accuracy_score(y_true, predictions)),
        "precision_churn": float(precision_score(y_true, predictions, zero_division=0)),
        "recall_churn": float(recall_score(y_true, predictions, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, probabilities)),
        "pr_auc": float(average_precision_score(y_true, probabilities)),
        "brier_score": float(brier_score_loss(y_true, probabilities)),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }


def run_training_pipeline(csv_path: str | Path | None = None) -> dict:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    raw_df = load_raw_data(csv_path)
    X, y = prepare_features_and_target(raw_df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    X_fit, X_valid, y_fit, y_valid = train_test_split(
        X_train, y_train, test_size=0.20, random_state=RANDOM_STATE, stratify=y_train
    )

    print(f"Rows: {len(raw_df):,} | features: {X.shape[1]} | train/test: {len(X_train):,}/{len(X_test):,}")
    print("Selecting XGBoost settings on the validation partition...")
    parameter_candidates = [
        XGBOOST_PARAMS,
        {**XGBOOST_PARAMS, "n_estimators": 500, "max_depth": 3, "learning_rate": 0.03, "min_child_weight": 3, "scale_pos_weight": 1.0},
        {**XGBOOST_PARAMS, "n_estimators": 400, "max_depth": 4, "learning_rate": 0.04, "min_child_weight": 1, "gamma": 0.0, "reg_alpha": 0.0, "scale_pos_weight": 1.0},
        {**XGBOOST_PARAMS, "n_estimators": 300, "max_depth": 3, "learning_rate": 0.05, "min_child_weight": 2, "subsample": 0.9, "colsample_bytree": 0.9, "scale_pos_weight": 1.0},
    ]
    candidate_results = []
    for params in parameter_candidates:
        candidate = build_xgb_pipeline(custom_params=params, calibrate=False)
        candidate.fit(X_fit, y_fit)
        candidate_prob = candidate.predict_proba(X_valid)[:, 1]
        candidate_results.append((accuracy_score(y_valid, candidate_prob >= 0.5), roc_auc_score(y_valid, candidate_prob), params))
    _, _, chosen_params = max(candidate_results, key=lambda row: (row[0], row[1]))
    print(f"Selected validation accuracy={max(candidate_results, key=lambda row: (row[0], row[1]))[0]:.3f}; fitting calibrated model...")
    candidate = build_xgb_pipeline(custom_params=chosen_params, calibrate=True)
    candidate.fit(X_fit, y_fit)
    validation_prob = candidate.predict_proba(X_valid)[:, 1]
    costs, _ = optimize_threshold(
        y_valid.to_numpy(), validation_prob,
        X_valid["MonthlyCharges"].to_numpy(),
    )
    threshold = float(costs["threshold"])

    print("Refitting calibrated XGBoost on the full training partition...")
    model = build_xgb_pipeline(custom_params=chosen_params, calibrate=True)
    model.fit(X_train, y_train)
    test_prob = model.predict_proba(X_test)[:, 1]
    xgb_default = _evaluate(y_test, test_prob, 0.50)
    xgb_policy = _evaluate(y_test, test_prob, threshold)

    shap_top_features = []
    try:
        import shap
        import matplotlib.pyplot as plt
        sample = X_test.sample(n=min(500, len(X_test)), random_state=RANDOM_STATE)
        transformed = transform_for_shap(model, sample)
        explainer = shap.TreeExplainer(get_tree_estimator(model))
        values = explainer(transformed, check_additivity=False)
        importance = pd.DataFrame({
            "feature": transformed.columns,
            "mean_absolute_shap": np.abs(values.values).mean(axis=0),
        }).sort_values("mean_absolute_shap", ascending=False)
        importance.to_csv(MODEL_DIR / "shap_feature_importance.csv", index=False)
        shap_top_features = importance.head(10).to_dict(orient="records")
        shap.summary_plot(values, transformed, plot_type="bar", max_display=15, show=False)
        plt.tight_layout()
        plt.savefig(MODEL_DIR / "shap_summary.png", dpi=160, bbox_inches="tight")
        plt.close()
    except Exception as exc:
        print(f"Global SHAP summary skipped: {exc}")

    baseline_candidate = build_lr_pipeline()
    baseline_candidate.fit(X_fit, y_fit)
    lr_validation_prob = baseline_candidate.predict_proba(X_valid)[:, 1]
    lr_policy_cost, _ = optimize_threshold(
        y_valid.to_numpy(), lr_validation_prob, X_valid["MonthlyCharges"].to_numpy()
    )
    lr_threshold = float(lr_policy_cost["threshold"])

    baseline = build_lr_pipeline()
    baseline.fit(X_train, y_train)
    lr_prob = baseline.predict_proba(X_test)[:, 1]
    lr_metrics = _evaluate(y_test, lr_prob, 0.50)
    lr_policy_metrics = _evaluate(y_test, lr_prob, lr_threshold)
    lr_policy_fn = lr_policy_metrics["confusion_matrix"]["fn"]
    xgb_policy_fn = xgb_policy["confusion_matrix"]["fn"]
    fn_reduction = ((lr_policy_fn - xgb_policy_fn) / lr_policy_fn * 100.0) if lr_policy_fn else 0.0
    default_lr_fn = lr_metrics["confusion_matrix"]["fn"]
    default_xgb_fn = xgb_default["confusion_matrix"]["fn"]
    default_fn_change = ((default_lr_fn - default_xgb_fn) / default_lr_fn * 100.0) if default_lr_fn else 0.0

    # Report the economic estimate on the untouched test set, using the
    # operating threshold chosen from validation data only.
    selected_outcome = compute_financial_outcomes(
        y_test.to_numpy(), test_prob, X_test["MonthlyCharges"].to_numpy(), threshold
    )
    everyone_outcome = compute_financial_outcomes(
        y_test.to_numpy(), test_prob, X_test["MonthlyCharges"].to_numpy(), 0.0
    )
    financial = {
        "assumptions": "Illustrative offer cost, success rate, and 30-month value assumptions; not realized savings.",
        "retention_policy_net_value": selected_outcome["net_value"],
        "savings_vs_do_nothing": selected_outcome["net_value"],
        "savings_vs_contact_everyone": selected_outcome["net_value"] - everyone_outcome["net_value"],
    }

    metrics = {
        "dataset_rows": int(len(raw_df)),
        "feature_count": int(X.shape[1]),
        "churn_rate": float(y.mean()),
        "test_rows": int(len(y_test)),
        "xgboost_default_threshold": xgb_default,
        "xgboost_cost_threshold": xgb_policy,
        "logistic_regression_threshold_0_5": lr_metrics,
        "logistic_regression_cost_threshold": lr_policy_metrics,
        "false_negative_reduction_pct_cost_policies": float(fn_reduction),
        "false_negative_reduction_pct_both_at_0_5": float(default_fn_change),
        "financial_estimate": financial,
        "selected_hyperparameters": chosen_params,
        "shap_top_features": shap_top_features,
    }
    threshold_data = {
        "threshold": threshold,
        "selection_data": "validation split from training data",
        "validation_net_value": float(costs["net_value"]),
        "logistic_regression_threshold": lr_threshold,
    }

    joblib.dump(model, CALIBRATED_PATH)
    joblib.dump(baseline, BASELINE_PATH)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    THRESHOLD_PATH.write_text(json.dumps(threshold_data, indent=2), encoding="utf-8")

    try:
        from sklearn.calibration import calibration_curve
        import matplotlib.pyplot as plt
        prob_true, prob_pred = calibration_curve(y_test, test_prob, n_bins=10, strategy="quantile")
        fig, ax = plt.subplots(figsize=(6, 5))
        ax.plot([0, 1], [0, 1], "--", color="gray", label="Perfect calibration")
        ax.plot(prob_pred, prob_true, "o-", label="Calibrated XGBoost")
        ax.set(xlabel="Mean predicted churn probability", ylabel="Observed churn fraction", title="Test-set calibration")
        ax.legend()
        fig.tight_layout()
        fig.savefig(MODEL_DIR / "calibration_curve.png", dpi=160)
        plt.close(fig)
    except Exception as exc:
        print(f"Calibration chart skipped: {exc}")

    print(json.dumps(metrics, indent=2))
    print(f"Saved model, metrics, and threshold under {MODEL_DIR}")
    return metrics


if __name__ == "__main__":
    run_training_pipeline()
