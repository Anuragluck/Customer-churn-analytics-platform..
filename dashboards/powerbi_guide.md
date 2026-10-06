# 📈 Power BI Executive KPI Dashboard Guide

This guide details how to build the executive-facing Power BI dashboard tracking **Overall Churn %**, **Revenue at Risk**, and **Customer Lifetime Value (CLV)** trends, connected directly to PostgreSQL.

---

## 🔌 1. Data Connection & DAX Measures

### Connection:
1. Open **Power BI Desktop** → **Get Data** → **PostgreSQL database**.
2. Server: `localhost:5432` | Database: `churn_db`.
3. Select tables `customers` and `churn_scores`.
4. Storage Mode: **DirectQuery** or **Import (scheduled refresh)**.

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
CALCULATE(
    SUM(churn_scores[revenue_at_risk]),
    churn_scores[is_high_risk] = 1
)

// 4. Customer Lifetime Value (CLV) at Risk
CLV at Risk = 
CALCULATE(
    SUM(churn_scores[clv_estimate]),
    churn_scores[is_high_risk] = 1
)

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
   - Card 1: `Overall Churn Rate %` (26.5%)
   - Card 2: `Monthly Revenue at Risk` ($142,500)
   - Card 3: `CLV at Risk` ($4.2M)
   - Card 4: `High Risk Customers` (Count: 1,480)

2. **Main Visuals (Middle Section):**
   - **Visual 1 (Donut Chart):** Risk Level Breakdown (`High`, `Medium`, `Low`) from `churn_scores`.
   - **Visual 2 (Clustered Column Chart):** Monthly Charges at Risk by `Contract Type`.
   - **Visual 3 (Line Chart):** Tenure vs. Cumulative Churn Rate trend.

3. **High-Risk Intervention Queue (Bottom Table):**
   - Table columns: `Customer ID`, `Contract`, `Tenure`, `Monthly Charges`, `Churn Probability %`, `CLV Estimate`.
   - Filtered to `is_high_risk = 1`, sorted descending by `Churn Probability`.
