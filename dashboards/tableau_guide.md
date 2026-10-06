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
- **Interpretation:** Compare the observed rates from the loaded sample; avoid treating this descriptive association as a causal contract effect.

### Sheet 2: Monthly Charges Distribution (Box Plot / Violin Plot)
- **Columns:** `Churn` (Yes / No)
- **Rows:** `Monthly Charges`
- **Mark:** Box Plot with individual customer jitter points.
- **Interpretation:** Read the medians from the live data rather than using a prefilled estimate.

### Sheet 3: Tenure Cohort Survival Curve (Kaplan-Meier View)
- Import the image exported from `model/survival_analysis.py` (`model/survival_by_contract.png`) or create a bin-based tenure step line chart.
- **Columns:** `Tenure` (0 to 72 months)
- **Rows:** `% Remaining Retained`
- **Color:** `Contract`

### Sheet 4: Service Bundling & Tech Support Heatmap
- **Columns:** `Internet Service` (DSL, Fiber optic, None)
- **Rows:** `Tech Support` (Yes, No)
- **Color Metric:** `Churn Rate %`
- **Interpretation:** Use the heatmap to find segments worth investigating; small groups should be interpreted with their customer counts.

---

## 🖥️ 3. Dashboard Layout
Combine Sheets 1–4 into a 1920x1080 Interactive Executive Layout with global filters for `Senior Citizen`, `Payment Method`, and `Tenure Cohort`.
