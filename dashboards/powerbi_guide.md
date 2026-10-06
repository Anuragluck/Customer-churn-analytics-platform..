# 📈 Power BI Executive KPI Dashboard Guide

This guide details the executive Power BI view for **Observed Churn %**, **Expected Revenue at Risk**, and **CLV at Risk**. Connect to the PostgreSQL semantic views for current local data, or import `dashboards/churn_analytics_dashboard.xlsx` for an offline copy.

---

## 🔌 1. Data Connection & DAX Measures

### Connection:
1. Open **Power BI Desktop** → **Get Data** → **PostgreSQL database**.
2. Server: `localhost:5432` | Database: `churn_db`.
3. Choose **Import** and select `v_customer_churn_analytics`, `v_churn_bi_kpis`, and `v_churn_contract_summary`.
4. Authenticate with **Database** credentials (`postgres` and the local `POSTGRES_PASSWORD` from `.env`). If Power BI requests a PostgreSQL provider, install the Npgsql provider linked from Microsoft's PostgreSQL connector documentation and restart Power BI.

For a workbook-backed prototype, select **Get Data → Excel workbook**, then import `Source Data`, `Customer Scores`, `Contract Summary`, and `Risk Summary`. The SQL views are already joined and need no relationship setup. They update whenever the source tables change; refresh the imported Power BI model after reloading or rescoring.

---

## 🧮 2. DAX Measures to Create

```dax
// 1. Total customers
Total Customers = DISTINCTCOUNT(v_customer_churn_analytics[customer_id])

// 2. Overall Churn Rate %
Overall Churn Rate % = 
DIVIDE(
    SUM(v_customer_churn_analytics[churn_flag]),
    [Total Customers],
    0
)

// 3. Total Monthly Revenue at Risk (From ML Predictions)
Monthly Revenue at Risk =
SUM(v_customer_churn_analytics[revenue_at_risk])

// 4. Customer Lifetime Value (CLV) at Risk
CLV at Risk =
SUM(v_customer_churn_analytics[clv_at_risk])

// 5. Count of customers above the saved operating threshold
High Risk Customers =
CALCULATE(
    DISTINCTCOUNT(v_customer_churn_analytics[customer_id]),
    v_customer_churn_analytics[is_high_risk] = 1
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
   - **Visual 1 (Donut Chart):** Risk Level Breakdown (`High`, `Medium`, `Low`) from `v_customer_churn_analytics[risk_level]`.
   - **Visual 2 (Clustered Column Chart):** Expected monthly revenue at risk by `contract` (use `v_churn_contract_summary`).
   - **Visual 3 (Bar Chart):** Observed churn rate by `tenure_band`; label it as a tenure segment comparison, not a time trend.

3. **High-Risk Intervention Queue (Bottom Table):**
   - Table columns: `Customer ID`, `Contract`, `Tenure`, `Monthly Charges`, `Churn Probability %`, `CLV at Risk`.
   - Filtered to `is_high_risk = 1`, sorted descending by `Churn Probability`.

The figures come from the loaded source and current score export. Do not copy sample values into cards; refresh the Power BI model after each scoring run. Revenue and CLV exposure are model-based estimates, not realized losses or retention savings. `CLV at Risk` inherits the remaining-month assumption documented in `src/config.py`.

## Refresh the workbook

```powershell
python -m model.score_customers --no-db
python dashboards/build_dashboard.py
```

The generated workbook contains the KPI cards and contract/risk summaries for offline review. Save the finished native report as `dashboards/churn_executive_dashboard.pbix` from Power BI Desktop.
