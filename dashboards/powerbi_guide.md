# 📈 Power BI Executive KPI Dashboard Guide

This guide details the executive Power BI view for **Observed Churn %**, **Expected Revenue at Risk**, and **CLV at Risk**. The refreshable workbook `dashboards/churn_analytics_dashboard.xlsx` is ready to import; use PostgreSQL for recurring database refreshes.

---

## 🔌 1. Data Connection & DAX Measures

### Connection:
1. Open **Power BI Desktop** → **Get Data** → **PostgreSQL database**.
2. Server: `localhost:5432` | Database: `churn_db`.
3. Select tables `customers` and `churn_scores`.
4. Storage Mode: **DirectQuery** or **Import (scheduled refresh)**.

For a workbook-backed prototype, select **Get Data → Excel workbook**, then import `Source Data`, `Customer Scores`, `Contract Summary`, and `Risk Summary`. For PostgreSQL, load customers and batch scores first. Relate `customers[customer_id]` to `churn_scores[customer_id]` as one-to-zero-or-one; scores cover only retained rows used as a teaching proxy for active customers.

---

## 🧮 2. DAX Measures to Create

```dax
// 1. Total Active Customers
Total Active Customers = 
CALCULATE(COUNTROWS(customers), customers[churn] = "No")

// 2. Overall Churn Rate %
Overall Churn Rate % = 
DIVIDE(
    CALCULATE(COUNTROWS(customers), customers[churn] = "Yes"),
    COUNTROWS(customers),
    0
)

// 3. Total Monthly Revenue at Risk (From ML Predictions)
Monthly Revenue at Risk = 
SUM(churn_scores[revenue_at_risk])

// 4. Customer Lifetime Value (CLV) at Risk
CLV at Risk = 
SUM(churn_scores[clv_at_risk])

// 5. Model Accuracy / Risk Coverage Ratio
High Risk Coverage % = 
DIVIDE(
    CALCULATE(COUNTROWS(churn_scores), churn_scores[is_high_risk] = 1),
    COUNTROWS(churn_scores),
    0
)
```

---

## 📊 3. Visual Canvas Layout

1. **Header Cards (Top Row):**
  - Card 1: `Overall Churn Rate %`
  - Card 2: `Monthly Revenue at Risk` (sum of probability-weighted monthly exposure)
  - Card 3: `Estimated CLV at Risk` (illustrative value under the configured remaining-month assumption)
  - Card 4: `High Risk Customers` (count using the saved operating threshold)

2. **Main Visuals (Middle Section):**
   - **Visual 1 (Donut Chart):** Risk Level Breakdown (`High`, `Medium`, `Low`) from `churn_scores`.
   - **Visual 2 (Clustered Column Chart):** Monthly Charges at Risk by `Contract Type`.
   - **Visual 3 (Line Chart):** Tenure vs. Cumulative Churn Rate trend.

3. **High-Risk Intervention Queue (Bottom Table):**
   - Table columns: `Customer ID`, `Contract`, `Tenure`, `Monthly Charges`, `Churn Probability %`, `CLV Estimate`.
   - Filtered to `is_high_risk = 1`, sorted descending by `Churn Probability`.

The figures come from the loaded source and current score export. Do not copy sample values into cards; refresh the PostgreSQL tables after each scoring run. Revenue and CLV exposure are model-based estimates, not realized losses or retention savings.

## Refresh the workbook

```powershell
python -m model.score_customers --no-db
python dashboards/build_dashboard.py
```

The generated workbook contains the KPI cards and contract/risk summaries for offline review. The public Streamlit app also includes a working executive KPI dashboard. Native `.pbix` authoring requires Power BI Desktop; use these field mappings to create and refresh that report from the workbook or PostgreSQL tables.
