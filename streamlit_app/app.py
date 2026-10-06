"""
app.py — Real-Time Customer Churn Prediction & Analytics Web App.

Deployed on Streamlit Community Cloud.
Features:
- Instant Customer Churn Risk Scoring (Calibrated XGBoost Model)
- Individual SHAP Waterfall & Force Plots for Feature Attribution
- Batch Active Customer Scoring & Revenue at Risk Lookup
- Executive KPI Overview Dashboard
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib
import shap
from pathlib import Path
import json
import sys
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))



from src.config import PROJECT_ROOT, CALIBRATED_PATH, METRICS_PATH, THRESHOLD_PATH
from src.costs import calculate_customer_clv

# Page Config
st.set_page_config(
    page_title="Customer Churn Prediction & Analytics",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paths
MODEL_PATH = CALIBRATED_PATH
SCORES_PATH = PROJECT_ROOT / "data" / "active_customer_scores.csv"
RAW_DATA_PATH = PROJECT_ROOT / "data" / "telco_churn.csv"

# ──────────────────────────────────────────────
# LOAD MODEL & ARTIFACTS
# ──────────────────────────────────────────────
@st.cache_resource
def load_pipeline():
    if not MODEL_PATH.exists():
        st.error(f"Model artifact not found at {MODEL_PATH}. Please run `python model/train.py` first.")
        st.stop()
    return joblib.load(MODEL_PATH)


@st.cache_data
def load_metrics():
    if METRICS_PATH.exists():
        return json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    return None


def load_policy_threshold():
    if THRESHOLD_PATH.exists():
        return float(json.loads(THRESHOLD_PATH.read_text(encoding="utf-8"))["threshold"])
    return 0.5


@st.cache_data
def load_data():
    if RAW_DATA_PATH.exists():
        return pd.read_csv(RAW_DATA_PATH)
    return None


@st.cache_data
def load_scores():
    if SCORES_PATH.exists():
        return pd.read_csv(SCORES_PATH)
    return None


pipeline = load_pipeline()
raw_df = load_data()
scores_df = load_scores()
metrics = load_metrics()
risk_threshold = load_policy_threshold()

# ──────────────────────────────────────────────
# HEADER & SIDEBAR NAVIGATION
# ──────────────────────────────────────────────
st.title("🎯 Customer Churn Intelligence & Analytics Platform")
test_accuracy = (metrics or {}).get("xgboost_default_threshold", {}).get("accuracy")
accuracy_text = f"Held-out test accuracy: **{test_accuracy:.1%}**. " if test_accuracy is not None else "Train the model to populate test metrics. "
st.markdown(
    f"{accuracy_text}Calibrated **XGBoost**, **SHAP explanations**, and optional **PostgreSQL integration**."
)

tab1, tab2, tab3 = st.tabs([
    "🔮 Live Churn Predictor",
    "📊 Executive KPI Dashboard",
    "📁 Customer Lookup & Batch Scoring"
])

# ──────────────────────────────────────────────
# TAB 1: LIVE CHURN PREDICTOR
# ──────────────────────────────────────────────
with tab1:
    st.subheader("Predict Individual Customer Churn Risk")
    st.markdown("Enter customer details in the sidebar to compute calibrated churn probability & SHAP breakdown.")

    col_input1, col_input2, col_input3 = st.columns(3)

    with col_input1:
        tenure = st.slider("Tenure (Months)", min_value=0, max_value=72, value=12)
        monthly_charges = st.number_input("Monthly Charges ($)", min_value=18.0, max_value=120.0, value=75.0)
        total_charges = st.number_input("Total Charges ($)", min_value=0.0, max_value=9000.0, value=float(tenure * monthly_charges))
        contract = st.selectbox("Contract Type", ["Month-to-month", "One year", "Two year"])
        payment_method = st.selectbox(
            "Payment Method",
            ["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"]
        )

    with col_input2:
        internet_service = st.selectbox("Internet Service", ["DSL", "Fiber optic", "No"])
        online_security = st.selectbox("Online Security", ["No", "Yes", "No internet service"])
        online_backup = st.selectbox("Online Backup", ["No", "Yes", "No internet service"])
        device_protection = st.selectbox("Device Protection", ["No", "Yes", "No internet service"])
        tech_support = st.selectbox("Tech Support", ["No", "Yes", "No internet service"])

    with col_input3:
        streaming_tv = st.selectbox("Streaming TV", ["No", "Yes", "No internet service"])
        streaming_movies = st.selectbox("Streaming Movies", ["No", "Yes", "No internet service"])
        paperless_billing = st.selectbox("Paperless Billing", ["Yes", "No"])
        senior_citizen = st.selectbox("Senior Citizen", ["No", "Yes"])
        partner = st.selectbox("Partner", ["Yes", "No"])
        dependents = st.selectbox("Dependents", ["No", "Yes"])
        phone_service = st.selectbox("Phone Service", ["Yes", "No"])
        multiple_lines = st.selectbox("Multiple Lines", ["No", "Yes", "No phone service"])

    # Construct Input DataFrame matching exact raw schema
    input_dict = {
        "gender": "Female",
        "SeniorCitizen": senior_citizen,
        "Partner": partner,
        "Dependents": dependents,
        "tenure": tenure,
        "PhoneService": phone_service,
        "MultipleLines": multiple_lines,
        "InternetService": internet_service,
        "OnlineSecurity": online_security,
        "OnlineBackup": online_backup,
        "DeviceProtection": device_protection,
        "TechSupport": tech_support,
        "StreamingTV": streaming_tv,
        "StreamingMovies": streaming_movies,
        "Contract": contract,
        "PaperlessBilling": paperless_billing,
        "PaymentMethod": payment_method,
        "MonthlyCharges": monthly_charges,
        "TotalCharges": total_charges,
    }

    input_df = pd.DataFrame([input_dict])

    if st.button("🚀 Calculate Churn Probability", type="primary"):
        # Run inference through calibrated pipeline
        prob = float(pipeline.predict_proba(input_df)[0, 1])
        pct_prob = prob * 100.0

        st.markdown("---")
        res_col1, res_col2, res_col3 = st.columns([1, 1, 2])

        with res_col1:
            st.metric(
                label="Calibrated Churn Risk",
                value=f"{pct_prob:.1f}%",
                delta="High Risk" if prob >= risk_threshold else "Low Risk",
                delta_color="inverse"
            )

        with res_col2:
            if prob >= max(0.60, risk_threshold):
                st.error("🚨 **CRITICAL RISK**: Trigger Immediate VIP Retention Campaign ($50 Offer)")
            elif prob >= risk_threshold:
                st.warning("⚠️ **ELEVATED RISK**: Trigger Tech Support / Contract Upgrade Outreach")
            else:
                st.success("✅ **SAFE**: Customer is stable. Standard Engagement.")

        with res_col3:
            clv_est = float(calculate_customer_clv(monthly_charges))
            rev_at_risk = monthly_charges * prob
            st.write(f"**Monthly Charges:** ${monthly_charges:,.2f}")
            st.write(f"**Estimated 30-Month CLV:** ${clv_est:,.2f}")
            st.write(f"**Revenue at Risk:** ${rev_at_risk:,.2f}/mo")

        # ──────────────────────────────────────────────
        # SHAP EXPLAINABILITY WATERFALL
        # ──────────────────────────────────────────────
        st.markdown("### 🧠 SHAP Feature Attribution (Why is this customer at risk?)")
        st.caption("SHAP attributes the underlying XGBoost output; because probabilities are calibrated afterward, the SHAP values are not additive parts of the displayed calibrated probability.")
        try:
            from src.model import get_tree_estimator, transform_for_shap
            
            tree_model = get_tree_estimator(pipeline)
            X_trans = transform_for_shap(pipeline, input_df)

            explainer = shap.TreeExplainer(tree_model)
            shap_values = explainer(X_trans)

            shap.plots.waterfall(shap_values[0], max_display=8, show=False)
            st.pyplot(plt.gcf())
            plt.close(plt.gcf())
        except Exception as e:
            st.info(f"SHAP explanation is unavailable for this prediction: {e}")

# ──────────────────────────────────────────────
# TAB 2: EXECUTIVE KPI DASHBOARD
# ──────────────────────────────────────────────
with tab2:
    st.subheader("Executive Churn & Revenue Intelligence")

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    if raw_df is not None:
        customer_count = len(raw_df)
        churn_rate = raw_df["Churn"].astype(str).str.strip().str.lower().eq("yes").mean()
    else:
        customer_count, churn_rate = 0, float("nan")
    default_eval = (metrics or {}).get("xgboost_default_threshold", {})
    expected_exposure = float(scores_df["revenue_at_risk"].sum()) if scores_df is not None else None
    kpi1.metric("Customers in source data", f"{customer_count:,}" if customer_count else "Dataset unavailable")
    kpi2.metric("Observed churn rate", f"{churn_rate:.1%}" if customer_count else "—")
    kpi3.metric("Held-out test accuracy", f"{default_eval['accuracy']:.1%}" if "accuracy" in default_eval else "Train model first")
    kpi4.metric("Expected monthly revenue exposure", f"${expected_exposure:,.0f}" if expected_exposure is not None else "Run batch scoring")
    financial = (metrics or {}).get("financial_estimate", {})
    if financial:
        st.caption(f"Illustrative policy value on held-out data: ${financial['savings_vs_do_nothing']:,.0f}. {financial['assumptions']}")

    if metrics:
        with st.expander("Held-out model evaluation"):
            eval_rows = []
            for name, item in [
                ("XGBoost, threshold 0.50", metrics.get("xgboost_default_threshold", {})),
                ("XGBoost, cost policy", metrics.get("xgboost_cost_threshold", {})),
                ("Logistic Regression, threshold 0.50", metrics.get("logistic_regression_threshold_0_5", {})),
                ("Logistic Regression, cost policy", metrics.get("logistic_regression_cost_threshold", {})),
            ]:
                if item:
                    eval_rows.append({
                        "Model / policy": name,
                        "Threshold": item.get("threshold"),
                        "Accuracy": item.get("accuracy"),
                        "Churn recall": item.get("recall_churn"),
                        "PR-AUC": item.get("pr_auc"),
                        "ROC-AUC": item.get("roc_auc"),
                        "False negatives": item.get("confusion_matrix", {}).get("fn"),
                    })
            st.dataframe(pd.DataFrame(eval_rows).set_index("Model / policy").style.format({
                "Threshold": "{:.2f}", "Accuracy": "{:.1%}", "Churn recall": "{:.1%}",
                "PR-AUC": "{:.3f}", "ROC-AUC": "{:.3f}",
            }), width="stretch")
            if metrics.get("shap_top_features"):
                st.write("Leading global SHAP features in the held-out sample:", ", ".join(row["feature"] for row in metrics["shap_top_features"][:5]))

    st.markdown("---")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("#### Churn Rate % by Contract Type")
        if raw_df is not None:
            contract_data = raw_df.assign(_churn=raw_df["Churn"].astype(str).str.strip().str.lower().eq("yes")).groupby("Contract", observed=True)["_churn"].mean().mul(100).rename("Churn rate %")
            st.bar_chart(contract_data)
        else:
            st.info("Add the source CSV to view contract churn rates.")

    with chart_col2:
        st.markdown("#### Monthly Charges Distribution (Churned vs Retained)")
        if raw_df is not None:
            charge_bins = pd.cut(raw_df["MonthlyCharges"], bins=12)
            charge_counts = raw_df.assign(_charge_bin=charge_bins).groupby(
                ["_charge_bin", "Churn"], observed=True
            ).size().unstack(fill_value=0)
            charge_counts.index = charge_counts.index.map(str)
            st.line_chart(charge_counts)
        else:
            st.info("Add the source CSV to view charge distributions.")

# ──────────────────────────────────────────────
# TAB 3: CUSTOMER LOOKUP & BATCH SCORES
# ──────────────────────────────────────────────
with tab3:
    st.subheader("Scored Customer Database & Search")

    if scores_df is not None:
        st.dataframe(scores_df, width="stretch")
    elif raw_df is not None:
        st.dataframe(raw_df.head(50), width="stretch")
    else:
        st.info("Run `python model/score_customers.py` to generate batch predictions.")
