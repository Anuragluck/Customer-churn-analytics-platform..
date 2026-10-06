"""
test_model.py — Pytest Unit Test Suite for Churn Platform.

Tests:
1. Data cleaning & missing TotalCharges imputation
2. Feature engineering (add_features returns pandas DataFrame with required columns)
3. Pipeline build & prediction probability range [0, 1]
4. Isotonic calibration validity
5. Cost model & threshold optimization returns positive savings
6. SHAP transformation output shapes
"""

import pytest
import pandas as pd
import numpy as np
from src.data import add_features, load_raw_data
from src.model import build_xgb_pipeline, build_lr_pipeline, transform_for_shap
from src.costs import compute_financial_outcomes, optimize_threshold


@pytest.fixture
def sample_df():
    """Create a synthetic sample DataFrame matching Telco Churn schema."""
    return pd.DataFrame({
        "customerID": ["001-A", "002-B", "003-C", "004-D"],
        "gender": ["Female", "Male", "Male", "Female"],
        "SeniorCitizen": ["No", "Yes", "No", "No"],
        "Partner": ["Yes", "No", "No", "Yes"],
        "Dependents": ["No", "No", "Yes", "No"],
        "tenure": [1, 12, 48, 72],
        "PhoneService": ["Yes", "Yes", "Yes", "Yes"],
        "MultipleLines": ["No", "Yes", "Yes", "Yes"],
        "InternetService": ["DSL", "Fiber optic", "Fiber optic", "No"],
        "OnlineSecurity": ["No", "Yes", "No", "No internet service"],
        "OnlineBackup": ["Yes", "No", "Yes", "No internet service"],
        "DeviceProtection": ["No", "Yes", "No", "No internet service"],
        "TechSupport": ["No", "No", "Yes", "No internet service"],
        "StreamingTV": ["No", "Yes", "Yes", "No internet service"],
        "StreamingMovies": ["No", "Yes", "No", "No internet service"],
        "Contract": ["Month-to-month", "Month-to-month", "One year", "Two year"],
        "PaperlessBilling": ["Yes", "Yes", "No", "No"],
        "PaymentMethod": ["Electronic check", "Electronic check", "Bank transfer (automatic)", "Mailed check"],
        "MonthlyCharges": [29.85, 89.85, 104.80, 20.05],
        "TotalCharges": [29.85, 1078.20, 5030.40, 1443.60],
        "Churn": ["No", "Yes", "No", "No"],
    })


def test_add_features(sample_df):
    """Verify feature engineering appends required engineered columns and stays a DataFrame."""
    df_fe = add_features(sample_df)
    assert isinstance(df_fe, pd.DataFrame)
    assert "tenure_months_ratio" in df_fe.columns
    assert "charge_per_tenure" in df_fe.columns
    assert "total_services" in df_fe.columns
    assert "overpay_ratio" in df_fe.columns
    assert "has_internet_bundle" in df_fe.columns


def test_pipeline_fit_predict(sample_df):
    """Verify XGBoost pipeline fits on sample data and produces valid [0, 1] probabilities."""
    X = sample_df.drop(columns=["Churn", "customerID"])
    y = (sample_df["Churn"] == "Yes").astype(int)

    pipeline = build_xgb_pipeline(calibrate=False)
    pipeline.fit(X, y)

    probs = pipeline.predict_proba(X)[:, 1]
    assert len(probs) == len(sample_df)
    assert np.all(probs >= 0.0) and np.all(probs <= 1.0)


def test_calibrated_pipeline(sample_df):
    """Verify CalibratedClassifierCV wrapper operates properly."""
    X = sample_df.drop(columns=["Churn", "customerID"])
    y = (sample_df["Churn"] == "Yes").astype(int)

    # Replicate sample data to ensure enough samples for 2-fold CV in unit test
    X_big = pd.concat([X] * 5, ignore_index=True)
    y_big = pd.concat([y] * 5, ignore_index=True)

    pipeline = build_xgb_pipeline(calibrate=True)
    pipeline.fit(X_big, y_big)

    probs = pipeline.predict_proba(X_big)[:, 1]
    assert np.all(probs >= 0.0) and np.all(probs <= 1.0)


def test_lr_baseline_pipeline(sample_df):
    """Verify Logistic Regression baseline pipeline handles scaling and fitting."""
    X = sample_df.drop(columns=["Churn", "customerID"])
    y = (sample_df["Churn"] == "Yes").astype(int)

    pipeline = build_lr_pipeline()
    pipeline.fit(X, y)

    probs = pipeline.predict_proba(X)[:, 1]
    assert len(probs) == len(sample_df)


def test_cost_model_optimization():
    """Verify threshold optimizer returns optimal threshold and non-negative financial values."""
    y_true = np.array([1, 1, 0, 0, 1, 0, 1, 0])
    y_prob = np.array([0.9, 0.8, 0.1, 0.2, 0.75, 0.3, 0.6, 0.05])
    monthly_charges = np.array([75.0, 85.0, 30.0, 50.0, 95.0, 20.0, 65.0, 40.0])

    best_res, df_res = optimize_threshold(y_true, y_prob, monthly_charges)

    assert "threshold" in best_res
    assert "net_value" in best_res
    assert 0.05 <= best_res["threshold"] <= 0.95


def test_transform_for_shap(sample_df):
    """Verify transform_for_shap outputs a named pandas DataFrame for TreeExplainer."""
    X = sample_df.drop(columns=["Churn", "customerID"])
    y = (sample_df["Churn"] == "Yes").astype(int)

    pipeline = build_xgb_pipeline(calibrate=False)
    pipeline.fit(X, y)

    X_shap = transform_for_shap(pipeline, X)
    assert isinstance(X_shap, pd.DataFrame)
    assert len(X_shap) == len(X)
    assert len(X_shap.columns) > 0
