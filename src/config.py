"""
config.py — Central configuration for the Churn Analytics Platform.

All column definitions, hyperparameters, cost assumptions, and file paths
live here so every other module imports from one place.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# ──────────────────────────────────────────────
# PATHS
# ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")
DATA_DIR = PROJECT_ROOT / "data"
MODEL_DIR = PROJECT_ROOT / "model"
RAW_CSV = DATA_DIR / "telco_churn.csv"

CALIBRATED_PATH = MODEL_DIR / "calibrated_model.joblib"
BASELINE_PATH = MODEL_DIR / "baseline_lr.pkl"
METRICS_PATH = MODEL_DIR / "metrics.json"
THRESHOLD_PATH = MODEL_DIR / "threshold.json"

# ──────────────────────────────────────────────
# COLUMN DEFINITIONS  (Kaggle Telco Customer Churn)
# ──────────────────────────────────────────────
ID_COL = "customerID"
TARGET = "Churn"

# Binary categorical (Yes / No)
BINARY_COLS = [
    "gender", "SeniorCitizen", "Partner", "Dependents",
    "PhoneService", "PaperlessBilling",
]

# Multi-class categorical
MULTI_COLS = [
    "MultipleLines",       # Yes / No / No phone service
    "InternetService",     # DSL / Fiber optic / No
    "OnlineSecurity",      # Yes / No / No internet service
    "OnlineBackup",        # Yes / No / No internet service
    "DeviceProtection",    # Yes / No / No internet service
    "TechSupport",         # Yes / No / No internet service
    "StreamingTV",         # Yes / No / No internet service
    "StreamingMovies",     # Yes / No / No internet service
    "Contract",            # Month-to-month / One year / Two year
    "PaymentMethod",       # 4 options
]

CAT_COLS = BINARY_COLS + MULTI_COLS

# Raw numeric columns
RAW_NUMERIC = ["tenure", "MonthlyCharges", "TotalCharges"]

# Engineered numeric features (added by src/data.py → add_features)
ENGINEERED_NUMERIC = [
    "tenure_months_ratio",      # tenure / 72 (max possible)
    "charge_per_tenure",        # MonthlyCharges / (tenure + 1)
    "total_services",           # count of subscribed services
    "overpay_ratio",            # MonthlyCharges * tenure / (TotalCharges + 1)
    "has_internet_bundle",      # binary: has internet + ≥2 add-ons
]

# Final numeric columns fed into ColumnTransformer
MODEL_NUMERIC = RAW_NUMERIC + ENGINEERED_NUMERIC

# All features used in model (order matters for ColumnTransformer)
ALL_FEATURES = MODEL_NUMERIC + CAT_COLS

# ──────────────────────────────────────────────
# SERVICE COLUMNS  (for feature engineering)
# ──────────────────────────────────────────────
SERVICE_COLS = [
    "PhoneService", "MultipleLines", "InternetService",
    "OnlineSecurity", "OnlineBackup", "DeviceProtection",
    "TechSupport", "StreamingTV", "StreamingMovies",
]

# ──────────────────────────────────────────────
# MODEL HYPERPARAMETERS  (candidate values; final configuration is selected on validation data)
# ──────────────────────────────────────────────
XGBOOST_PARAMS = {
    "n_estimators": 300,
    "max_depth": 5,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_weight": 3,
    "gamma": 0.1,
    "reg_alpha": 0.1,
    "reg_lambda": 1.0,
    "scale_pos_weight": 1.0,
    "eval_metric": "logloss",
    "random_state": 42,
    "n_jobs": -1,
}

LOGISTIC_PARAMS = {
    "C": 1.0,
    "max_iter": 1000,
    "class_weight": "balanced",
    "random_state": 42,
    "solver": "lbfgs",
}

# ──────────────────────────────────────────────
# COST ASSUMPTIONS  (for threshold optimization)
# ──────────────────────────────────────────────
RETENTION_OFFER_COST = 50.0         # $ cost of one retention offer
RETENTION_SUCCESS_RATE = 0.35       # 35% of contacted at-risk customers stay
AVG_CUSTOMER_LIFETIME_MONTHS = 30   # expected remaining months if retained
DISCOUNT_RATE_ANNUAL = 0.10         # for CLV discounting

# ──────────────────────────────────────────────
# TRAIN / TEST SPLIT
# ──────────────────────────────────────────────
TEST_SIZE = 0.20
RANDOM_STATE = 42
CALIBRATION_CV = 5

# ──────────────────────────────────────────────
# DATABASE (PostgreSQL)
# ──────────────────────────────────────────────
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "churn_db",
    "user": "postgres",
    "password": os.getenv("POSTGRES_PASSWORD", ""),
}

DB_URI = os.getenv("DATABASE_URL") or (
    f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)
