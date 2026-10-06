# 🎯 Customer Churn Prediction & Analytics Platform

An end-to-end, production-grade churn intelligence system combining predictive machine learning, probability calibration, survival analysis, executive business intelligence dashboards, and a real-time web application.

---

## 📌 Executive Summary & Key Highlights
* **Predictive Performance:** Trained an XGBoost classifier with probability calibration reaching **86%+ accuracy** on 7,043 customer records / 20 features, achieving an **~18% reduction in false negatives** compared to a Logistic Regression baseline.
* **Explainability (SHAP):** Identified `tenure`, `monthly charges`, and `contract type` as the primary drivers of customer departure.
* **Database & Analytics Layer:** PostgreSQL data warehouse with automated scoring pipeline (`churn_scores`) queried through **15+ business-critical SQL queries**.
* **Business Intelligence:**
  * **Power BI:** Executive KPI dashboard tracking overall churn rate %, revenue at risk, and Customer Lifetime Value (CLV) trends.
  * **Tableau:** Visual exploratory data analysis (EDA) featuring tenure-based cohort survival analysis.
* **Live Deployment:** Real-time **Streamlit web application** providing instant churn probability scoring and individual customer SHAP waterfall explanations.
* **Engineering Standards:** Full Scikit-Learn `Pipeline` (zero data leakage), cost-benefit threshold optimization, Docker containerization, and unit test coverage.

---

## 🏗️ Architecture

```
Raw Data (Kaggle Telco Churn CSV)
         │
         ▼
 ┌───────────────┐
 │  PostgreSQL   │ ◄─── (Stores raw customer records & analytical views)
 └───────┬───────┘
         │
         ▼
 ┌───────────────┐
 │ Scikit-Learn  │ ─── Features (Encoding, Scaler) ──► XGBoost + Isotonic Calibration
 │   Pipeline    │ ─── SHAP Explainability ──────────► Feature Importance
 └───────┬───────┘
         │
         ├───────────────────────────────────────────────┐
         ▼                                               ▼
 ┌────────────────┐                              ┌───────────────┐
 │  PostgreSQL    │                              │ Streamlit App │
 │ (churn_scores) │                              │ (Live Scoring │
 └───────┬────────┘                              │   & SHAP UI)  │
         │                                       └───────────────┘
         ├──────────────────────────┐
         ▼                          ▼
 ┌───────────────┐          ┌───────────────┐
 │   Power BI    │          │    Tableau    │
 │ (Revenue Risk │          │ (Cohort & EDA │
 │  & CLV KPIs)  │          │   Analysis)   │
 └───────────────┘          └───────────────┘
```

---

## 🛠️ Tech Stack
* **Language & Core:** Python 3.10+, Pandas, NumPy, Scipy
* **Machine Learning & Explainability:** XGBoost, Scikit-learn, SHAP, Joblib
* **Survival Analysis:** Lifelines (Kaplan-Meier, Cox Proportional Hazards)
* **Database & SQL:** PostgreSQL, SQLAlchemy, Psycopg2
* **Visualization & Apps:** Streamlit, Tableau, Power BI, Matplotlib, Seaborn
* **DevOps & Testing:** Docker, Pytest

---

## 🚀 Repository Structure
```
├── data/                    # Raw & processed datasets
├── sql/                     # PostgreSQL schema, ingestion & 15+ analytical queries
├── src/                     # Core ML pipeline modules
│   ├── data.py              # Ingestion, cleaning, feature engineering
│   ├── model.py             # Pipeline assembly, XGBoost, calibration
│   └── costs.py             # Financial cost matrix & threshold optimizer
├── model/                   # Serialized pipelines (joblib) & evaluation artifacts
├── notebooks/               # EDA & cohort survival analysis
├── dashboards/              # Tableau & Power BI documentation, templates, and guides
├── streamlit_app/           # Interactive customer churn prediction web app
├── tests/                   # Pytest suite
├── Dockerfile               # Production containerization
├── requirements.txt         # Project dependencies
└── README.md
```
