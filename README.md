# Customer Churn Prediction & Analytics Platform

This is my end-to-end data science project about customer churn. I used the IBM Telco Customer Churn sample to train a model, look at the reasons behind its predictions, and make a small app where a user can try a prediction.

I wanted to practice more than model training, so the project also has a PostgreSQL database, SQL analysis, batch scoring, and dashboard files and guides.

## What the project does

- Trains an XGBoost churn classifier on 7,043 customer records with 19 input features. The customer ID and churn label are not used as model inputs.
- Compares XGBoost with a Logistic Regression baseline and reports accuracy, churn recall, ROC-AUC, PR-AUC, calibration, and confusion matrices.
- Uses SHAP to explain model output. In this run, contract type and the engineered `charge_per_tenure` feature ranked highly. Online security, internet service, tech support, monthly charges, and tenure also appear in the feature results.
- Saves the trained model with joblib and uses the same preprocessing pipeline for predictions.
- Scores the retained customers in the sample and writes their risk and revenue exposure to PostgreSQL.
- Includes 15 SQL analysis queries, PostgreSQL views for BI tools, a refreshable Excel dashboard, and Power BI and Tableau connection guides.
- Includes a Streamlit app for individual predictions, SHAP explanations, model metrics, and customer score review.

## Model results

These numbers come from the current saved run, using a held-out test set of 1,409 rows. The default 0.50 threshold results are:

| Model | Accuracy | ROC-AUC | PR-AUC | Churn recall | False negatives |
|---|---:|---:|---:|---:|---:|
| XGBoost | 80.2% | 0.841 | 0.647 | 55.6% | 166 |
| Logistic Regression | 74.0% | 0.847 | 0.666 | 77.5% | 84 |

At the default threshold, XGBoost had higher accuracy, while Logistic Regression had better churn recall and PR-AUC on this split. I also tried a cost-based threshold for prioritizing recall. The chosen XGBoost threshold was 0.07 and caught more churners, but it also flagged many customers who did not churn. The cost calculation depends on example offer-cost and customer-value assumptions; it is not measured business savings.

The model is a learning project using a static public sample. It does not prove that a retention offer prevents churn, and the results may change with a different split or dataset.

## Data and database

The CSV has 7,043 customers, one customer ID column, 19 predictor columns, and the churn label. The data is a public sample, not a real business customer list.

The database has two main tables:

- `customers` stores the source customer records.
- `churn_scores` stores model probability, risk category, monthly revenue exposure, and estimated CLV at risk.

The BI views are `v_customer_churn_analytics`, `v_churn_bi_kpis`, and `v_churn_contract_summary`. The customer view joins source rows to model scores. Scores are produced for rows labelled retained in this sample as a stand-in for current active customers; the dataset does not include point-in-time snapshots.

## Run it locally with Docker

You need Docker Desktop running. From the project folder, run these commands in PowerShell:

```powershell
docker compose up --build -d
docker compose run --rm app python -m scripts.load_data --create-schema
docker compose run --rm app python -m model.score_customers
```

The schema command creates the tables and BI views, then loads or updates the customer data. The scoring command writes scores to PostgreSQL and updates `data/active_customer_scores.csv`.

Open the app at [http://localhost:8501](http://localhost:8501).

To stop the containers later:

```powershell
docker compose down
```

## Run Python without Docker

Use Python 3.10 or later. In a virtual environment, install the packages and start the app:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m model.train
python -m model.score_customers --no-db
streamlit run streamlit_app/app.py
```

The `--no-db` option writes the score CSV without needing PostgreSQL. To load data into PostgreSQL, set `DATABASE_URL` in your local `.env` file.

## Dashboards

The repo includes `dashboards/churn_analytics_dashboard.xlsx`, which can be opened in Excel and imported into Power BI or Tableau. It also has SQL views and setup guides for connecting those tools to PostgreSQL:

- [Power BI guide](dashboards/powerbi_guide.md)
- [Tableau guide](dashboards/tableau_guide.md)

The guides describe report layouts for churn rate, predicted risk, revenue exposure, tenure groups, and a high-risk customer list. The repository currently contains the Excel dashboard and the Power BI/Tableau guides; it does not contain saved `.pbix` or `.twbx` report files.

## Streamlit deployment

The app runs locally at `http://localhost:8501`. A Streamlit Community Cloud URL is configured, but it showed a crash page at the last check. I have not confirmed that the hosted version is working; the local app is the reliable demo for now.

## Project folders

```text
data/                 Source customer data and batch score export
dashboards/           Excel dashboard, build script, and BI connection guides
model/                Training, scoring, evaluation, and saved model files
notebooks/            Starter exploratory analysis notebook
scripts/              PostgreSQL data loader
sql/                  Database schema, analysis queries, and BI views
src/                  Feature engineering, model setup, and cost assumptions
streamlit_app/        Streamlit prediction and analytics app
tests/                Model-related checks
```

## A few things I learned

- Accuracy alone did not tell the full story because churn is the smaller class. Recall, PR-AUC, and false negatives helped explain the model trade-off.
- Contract type and service choices were useful areas to explore, but the dataset only shows associations. They do not establish why a customer churned.
- Revenue at risk is probability-weighted exposure, and CLV at risk uses an assumed remaining customer lifetime. They are estimates, not realized losses.
- The cohort chart groups customers by their recorded tenure. The data has no signup dates, so it is not a calendar-based cohort or longitudinal survival study.

## Possible next improvements

- Finish and save the native Power BI and Tableau reports from the included guides.
- Check the Streamlit Community Cloud logs and restore the hosted demo.
- Try the model on newer customer data and validate the retention assumptions with an actual experiment.
