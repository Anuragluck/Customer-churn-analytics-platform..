# 📊 Tableau Dashboard Implementation Guide

Use this guide to connect Tableau to PostgreSQL for refreshable analysis. A ready-to-open Excel dashboard and BI-ready tables are also included at `dashboards/churn_analytics_dashboard.xlsx` if you want to explore before PostgreSQL is running.

---

## 🔌 1. Database Connection Setup
1. Open **Tableau Desktop**.
2. Under **To a Server**, select **PostgreSQL**.
3. Enter Connection Parameters:
   - **Server:** `localhost`
   - **Port:** `5432`
   - **Database:** `churn_db`
   - **Username:** `postgres`
   - **Password:** `<your_password>`
4. Drag and drop the `customers` table into the Canvas.
5. Create a **Left Join** between `customers` and `churn_scores` on `customer_id = customer_id`.

Before joining, load customers with `python -m scripts.load_data --create-schema`, then publish model scores with `python -m model.score_customers`. The join is one-to-zero-or-one because `churn_scores` contains only retained rows used as the project's active-customer proxy. Keep observed churn charts based on `customers`; use `churn_scores` for predicted risk and exposure.

---

## 📈 2. Visual Worksheets to Build

### Sheet 1: Churn Rate by Contract Type (Bar Chart)
- **Columns:** `Contract`
- **Rows:** `SUM(IIF([churn] = 'Yes', 1, 0)) / COUNTD([customer_id])`
- **Mark:** Bar Chart
- **Color:** Red for Month-to-Month, Blue/Grey for 1-Yr and 2-Yr.
- **Interpretation:** Compare the observed rates from the loaded sample; avoid treating this descriptive association as a causal contract effect.

### Sheet 2: Monthly Charges Distribution (Box Plot / Violin Plot)
- **Columns:** `Churn` (Yes / No)
- **Rows:** `Monthly Charges`
- **Mark:** Box Plot with individual customer jitter points.
- **Interpretation:** Read the medians from the live data rather than using a prefilled estimate.

### Sheet 3: Tenure Survival View
- Use the generated Kaplan–Meier figure at `model/survival_by_contract.png` as a dashboard image, or rebuild a descriptive tenure curve from `customers`.
- **Important:** The sample has no event dates or customer snapshots. A tenure curve by contract is exploratory and should not be described as a longitudinal cohort estimate.

### Sheet 4: Service Bundling & Tech Support Heatmap
- **Columns:** `Internet Service` (DSL, Fiber optic, None)
- **Rows:** `Tech Support` (Yes, No)
- **Color Metric:** `Churn Rate %`
- **Interpretation:** Use the heatmap to find segments worth investigating; small groups should be interpreted with their customer counts.

---

## 🖥️ 3. Dashboard Layout
Combine Sheets 1–4 into a 1920x1080 Interactive Executive Layout with global filters for `Senior Citizen`, `Payment Method`, and `Tenure Cohort`.

## Refreshable workbook

To rebuild the accompanying dashboard after new scores are generated, run:

```powershell
python -m model.score_customers --no-db
python dashboards/build_dashboard.py
```

Open `churn_analytics_dashboard.xlsx` in Excel, or connect Tableau to its `Source Data`, `Customer Scores`, `Contract Summary`, and `Risk Summary` sheets. The workbook charts summarize the bundled sample and score export; direct PostgreSQL connections are preferred for recurring refreshes.
