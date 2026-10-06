# 📊 Tableau Dashboard Implementation Guide

Use this guide to connect Tableau to PostgreSQL for refreshable analysis. The PostgreSQL semantic views give Tableau one row per customer plus ready-made KPI and contract summaries. A refreshable Excel dashboard is also included at `dashboards/churn_analytics_dashboard.xlsx` for offline exploration.

---

## 🔌 1. Database Connection Setup
1. Open **Tableau Desktop / Tableau Free Edition**.
2. Under **To a Server**, select **PostgreSQL**.
3. Enter Connection Parameters:
   - **Server:** `localhost`
   - **Port:** `5432`
   - **Database:** `churn_db`
   - **Username:** `postgres`
   - **Password:** the local `POSTGRES_PASSWORD` value in `.env` (do not save it in the workbook).
4. Select `v_customer_churn_analytics` as the main source. Add `v_churn_bi_kpis` and `v_churn_contract_summary` as separate data sources when building KPI/contract sheets; avoid physically joining aggregate views to customer rows.
5. Select **Live** for the local database connection.

Before connecting, load customers and create the views with `docker compose run --rm app python -m scripts.load_data --create-schema`, then publish model scores with `docker compose run --rm app python -m model.score_customers`. The joined customer view keeps observed churn for all sample rows and model risk/exposure for the retained-row active-customer proxy. If Tableau asks for a PostgreSQL driver, install its official PostgreSQL driver and restart Tableau.

---

## 📈 2. Visual Worksheets to Build

### Sheet 1: Churn Rate by Contract Type (Bar Chart)
- **Columns:** `contract`
- **Rows:** `AVG([churn_flag])` (format as percentage)
- **Mark:** Bar Chart
- **Color:** Red for Month-to-Month, Blue/Grey for 1-Yr and 2-Yr.
- **Interpretation:** Compare the observed rates from the loaded sample; avoid treating this descriptive association as a causal contract effect.

### Sheet 2: Monthly Charges Distribution (Box Plot / Violin Plot)
- **Columns:** `churn` (Yes / No)
- **Rows:** `monthly_charges`
- **Mark:** Box Plot with individual customer jitter points.
- **Interpretation:** Read the medians from the live data rather than using a prefilled estimate.

### Sheet 3: Observed Churn by Tenure Band
- **Columns:** `tenure_band`
- **Rows:** `AVG([churn_flag])` (format as percentage; sort by band order)
- This compares tenure segments, not a time trend. The sample has no event dates or customer snapshots.

### Sheet 4: Service Bundling & Tech Support Heatmap
- **Columns:** `internet_service` (DSL, Fiber optic, None)
- **Rows:** `tech_support` (Yes, No)
- **Color Metric:** `AVG([churn_flag])` (format as percentage)
- **Interpretation:** Use the heatmap to find segments worth investigating; small groups should be interpreted with their customer counts.

---

## 🖥️ 3. Dashboard Layout
Combine Sheets 1–4 into an interactive dashboard with filters for `senior_citizen`, `payment_method`, and `tenure_band`. Add score and exposure cards from `v_churn_bi_kpis` and use `v_churn_contract_summary` for revenue-at-risk by contract. Add a high-risk table filtered to `is_high_risk = 1`, with customer ID, contract, tenure, monthly charges, probability, and CLV at risk. Save a packaged workbook locally as `dashboards/churn_analytics_tableau.twbx`.

## Refreshable workbook

To rebuild the accompanying dashboard after new scores are generated, run:

```powershell
python -m model.score_customers --no-db
python dashboards/build_dashboard.py
```

Open `churn_analytics_dashboard.xlsx` in Excel, or connect Tableau to its `Source Data`, `Customer Scores`, `Contract Summary`, and `Risk Summary` sheets. The workbook charts summarize the bundled sample and score export; direct PostgreSQL connections are preferred for recurring refreshes.
