"""
model.py — Scikit-Learn Pipeline Builders, Calibration, and SHAP Helpers.

Ensures zero data leakage: feature engineering, encoding, and scaling
all happen strictly inside fit().
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

from src.config import (
    CAT_COLS, MODEL_NUMERIC, XGBOOST_PARAMS, LOGISTIC_PARAMS,
    CALIBRATION_CV, RANDOM_STATE
)
from src.data import add_features


def build_preprocessor(scale: bool = False) -> ColumnTransformer:
    """
    Builds a ColumnTransformer for categorical and numeric features.
    
    scale=False for XGBoost (trees are scale-invariant).
    scale=True for Logistic Regression (requires scaling for convergence).
    """
    numeric_transformer = StandardScaler() if scale else "passthrough"

    return ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT_COLS),
            ("num", numeric_transformer, MODEL_NUMERIC),
        ],
        verbose_feature_names_out=False,
    )


def make_xgb_classifier(custom_params: dict | None = None) -> XGBClassifier:
    """Instantiate XGBClassifier with tuned hyper-parameters."""
    params = XGBOOST_PARAMS.copy()
    if custom_params:
        params.update(custom_params)
    return XGBClassifier(**params)


def build_xgb_pipeline(
    custom_params: dict | None = None,
    calibrate: bool = True
) -> Pipeline:
    """
    Build end-to-end XGBoost pipeline.
    
    If calibrate=True, wraps classifier in CalibratedClassifierCV using 
    isotonic regression (cv=5, ensemble=False).
    """
    clf = make_xgb_classifier(custom_params)
    if calibrate:
        clf = CalibratedClassifierCV(clf, method="isotonic", cv=CALIBRATION_CV, ensemble=False)

    return Pipeline(
        steps=[
            ("feature_eng", FunctionTransformer(add_features)),
            ("preprocessor", build_preprocessor(scale=False)),
            ("classifier", clf),
        ]
    )


def build_lr_pipeline() -> Pipeline:
    """Logistic Regression baseline pipeline: the baseline XGBoost must beat."""
    clf = LogisticRegression(**LOGISTIC_PARAMS)
    return Pipeline(
        steps=[
            ("feature_eng", FunctionTransformer(add_features)),
            ("preprocessor", build_preprocessor(scale=True)),
            ("classifier", clf),
        ]
    )


def get_tree_estimator(pipeline: Pipeline) -> XGBClassifier:
    """
    Extract the raw XGBClassifier from a fitted (possibly calibrated) pipeline
    so SHAP TreeExplainer can inspect tree structures directly.
    """
    model = pipeline.named_steps["classifier"]
    if hasattr(model, "calibrated_classifiers_"):
        return model.calibrated_classifiers_[0].estimator
    return model


def transform_for_shap(pipeline: Pipeline, X: pd.DataFrame) -> pd.DataFrame:
    """
    Transform input raw DataFrame through pipeline preprocessing steps
    and return a named DataFrame ready for SHAP TreeExplainer.
    """
    prep = pipeline.named_steps["preprocessor"]
    
    # Run feature engineering + column transformer (slice up to classifier)
    X_fe = pipeline.named_steps["feature_eng"].transform(X)
    X_trans = prep.transform(X_fe)

    feature_names = prep.get_feature_names_out()
    return pd.DataFrame(X_trans, columns=feature_names, index=X.index)
