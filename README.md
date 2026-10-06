# Customer Churn Prediction & Analytics Platform

An end-to-end portfolio project for identifying customers at risk of leaving, explaining individual predictions, estimating retention campaign value, and exposing customer scores to PostgreSQL and BI tools.

## What is included

- A preprocessing and prediction pipeline with one-hot encoding, feature engineering, XGBoost, and isotonic probability calibration.
- A Logistic Regression baseline and held-out evaluation using churn recall, PR-AUC, ROC-AUC, Brier score, accuracy, and confusion matrices.
- A cost-based contact threshold selected from a validation partition and reused in batch scoring and the Streamlit app.
- Batch scoring of active rows, probability-weighted monthly revenue exposure, estimated customer value, and PostgreSQL upserts.
- A Streamlit prediction app with SHAP explanations and data-driven dashboard KPIs.
- PostgreSQL schema, repeatable data ingestion, 15 analytical SQL queries, Tableau and Power BI build guides, survival analysis, and a starter EDA notebook.

## Data

The repository includes the IBM Telco Customer Churn sample dataset (7,043 records; one identifier, 19 predictors, and the churn target). Source: [IBM Telco Customer Churn sample](https://github.com/IBM/telco-customer-churn-on-icp4d). The data is for demonstration and model development; it is not a production customer list.

## Quick start

Use Python 3.10 or later. From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m model.train
python -m model.score_customers --no-db
streamlit run streamlit_app/app.py
```

Training writes the calibrated model, baseline model, threshold policy, test metrics, and calibration plot under `model/`. Batch scoring writes `data/active_customer_scores.csv`. The Streamlit app reads those generated artifacts and the bundled source data.

## Model evaluation and business assumptions

The test set is held out from threshold selection. The threshold is chosen on a validation split using the offer cost, estimated offer success rate, and remaining customer value configured in `src/config.py`. The financial output is an **illustrative expected value under those assumptions**, not realized savings or a causal estimate of campaign impact. The app reads actual metrics from `model/metrics.json`; no metric is hardcoded as a result.

Current reproducible holdout results (seed 42, 1,409 test customers):

| Model / policy | Accuracy | ROC-AUC | PR-AUC | Churn recall | False negatives |
|---|---:|---:|---:|---:|---:|
| XGBoost, threshold 0.50 | 80.2% | 0.841 | 0.647 | 55.6% | 166 |
| Logistic Regression, threshold 0.50 | 74.0% | 0.847 | 0.666 | 77.5% | 84 |
| XGBoost, cost threshold 0.07 | 54.5% | 0.841 | 0.647 | 96.3% | 14 |
| Logistic Regression, cost threshold 0.15 | 54.9% | 0.847 | 0.666 | 97.6% | 9 |

On this fixed split, XGBoost has higher accuracy at 0.50, while Logistic Regression has stronger ROC-AUC, PR-AUC, and churn recall. The cost-selected policies contact many customers; the reported XGBoost policy did **not** reduce false negatives versus the Logistic Regression cost policy. These are the observed results, not a guaranteed target. Global SHAP ranked month-to-month contract, `charge_per_tenure`, lack of online security, fiber service, and lack of tech support among the leading drivers.

After training, review `model/metrics.json` before updating a résumé or presenting a specific performance figure. In particular, compare churn recall and PR-AUC with the Logistic Regression baseline, and report the false-negative change at the same 0.50 threshold. Accuracy is included but should not be treated as the only measure on an imbalanced dataset.

The default split is stratified and reproducible. This benchmark is a static cross-sectional dataset, so results do not establish how a model will perform on future customers or prove that a retention offer prevents churn.

## PostgreSQL

1. Install Docker Desktop and copy `.env.example` to `.env`; replace its local development password.
2. Start PostgreSQL and the app, then load/update source rows:

```powershell
docker compose up --build -d
docker compose run --rm app python -m scripts.load_data --create-schema
docker compose run --rm app python -m model.score_customers
```

Open `http://localhost:8501`. For an installed PostgreSQL instead, set `DATABASE_URL` in `.env` to its connection string and run the Python module commands directly.

The scorer also saves a CSV if PostgreSQL is unavailable. It does not drop or replace the `churn_scores` table. It scores rows marked retained in the source CSV to simulate a current active-customer population; this is a teaching proxy because the public sample has no point-in-time snapshots.

## Other components

- **Survival analysis:** `python -m model.survival_analysis` exports a Kaplan–Meier chart and estimates a Cox model. This is exploratory: the public data lacks event dates and contract changes over time.
- **Streamlit:** Shows individual prediction probability and SHAP drivers, observed contract churn rates, test metrics, and batch score exports.
- **Tableau / Power BI:** Follow the connection and visual instructions in `dashboards/`. The guides describe how to build dashboards; they are not packaged `.twb` or `.pbix` files.
- **Notebook:** `notebooks/EDA_and_Model.ipynb` contains initial EDA; use the Python training module as the source of truth for model results.
- **Docker:** `docker compose up --build` starts the app and PostgreSQL together.

### Streamlit Community Cloud

Push the repository to GitHub, create a new Streamlit Community Cloud app from that repository, choose the `main` branch and `streamlit_app/app.py`, and deploy. The app and trained artifacts are in the repository; PostgreSQL is optional for the demo. After replacing the model, rerun training and commit the updated joblib model together with `model/metrics.json` and `model/threshold.json` so the app and score policy stay in sync.

## Repository layout

```text
data/                 Source dataset and generated score export
dashboards/           Tableau and Power BI guides
model/                Training, scoring, survival analysis, generated artifacts
notebooks/            EDA notebook
scripts/              PostgreSQL ingestion command
sql/                  Schema and business queries
src/                  Feature engineering, model pipeline, business costs
streamlit_app/        Interactive prediction and analytics UI
tests/                Automated regression tests
```

## Limitations and recommendations

- Treat risk scores as prioritization signals, not certainty about an individual customer.
- Validate the cost assumptions with a real retention team and run an experiment before claiming campaign savings.
- Monitor calibration and model performance when new customer data becomes available.
- A useful business action to evaluate is moving month-to-month customers toward longer contracts, while testing whether the offer improves retention.
