# 📊 Tableau Dashboard Implementation Guide

This guide details how to connect Tableau to the PostgreSQL database and build the Visual Exploratory Data Analysis (EDA) dashboard with Kaplan-Meier survival cohort analysis.

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

---

## 📈 2. Visual Worksheets to Build

### Sheet 1: Churn Rate by Contract Type (Bar Chart)
- **Columns:** `Contract`
- **Rows:** `AVG(Number of Records)` or Calculated Field: `SUM(IF [Churn] = 'Yes' THEN 1 ELSE 0 END) / COUNT([Customer Id])`
- **Mark:** Bar Chart
- **Color:** Red for Month-to-Month, Blue/Grey for 1-Yr and 2-Yr.
- **Insight:** Month-to-month contracts exhibit ~42.7% churn, compared to <3% for 2-year contracts.

### Sheet 2: Monthly Charges Distribution (Box Plot / Violin Plot)
- **Columns:** `Churn` (Yes / No)
- **Rows:** `Monthly Charges`
- **Mark:** Box Plot with individual customer jitter points.
- **Insight:** Churned customers have a significantly higher median monthly charge (~$80 vs ~$60).

### Sheet 3: Tenure Cohort Survival Curve (Kaplan-Meier View)
- Import the image exported from `model/survival_analysis.py` (`model/survival_by_contract.png`) or create a bin-based tenure step line chart.
- **Columns:** `Tenure` (0 to 72 months)
- **Rows:** `% Remaining Retained`
- **Color:** `Contract`

### Sheet 4: Service Bundling & Tech Support Heatmap
- **Columns:** `Internet Service` (DSL, Fiber optic, None)
- **Rows:** `Tech Support` (Yes, No)
- **Color Metric:** `Churn Rate %`
- **Insight:** Fiber optic customers *without* Tech Support have the highest churn rate across the entire user base (~49.3%).

---

## 🖥️ 3. Dashboard Layout
Combine Sheets 1–4 into a 1920x1080 Interactive Executive Layout with global filters for `Senior Citizen`, `Payment Method`, and `Tenure Cohort`.
