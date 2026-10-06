-- ============================================================================
-- 03_analytical_queries.sql — 15+ Executive & Operational Business SQL Queries
-- ============================================================================

-- Q1: Overall Churn Rate % & Total Revenue Lost
SELECT 
    COUNT(*) AS total_customers,
    SUM(CASE WHEN churn = 'Yes' THEN 1 ELSE 0 END) AS churned_customers,
    ROUND(SUM(CASE WHEN churn = 'Yes' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS churn_rate_pct,
    SUM(CASE WHEN churn = 'Yes' THEN monthly_charges ELSE 0 END) AS monthly_revenue_lost
FROM customers;


-- Q2: Churn Rate by Contract Type (Month-to-Month vs 1-Yr vs 2-Yr)
SELECT 
    contract,
    COUNT(*) AS total_customers,
    SUM(CASE WHEN churn = 'Yes' THEN 1 ELSE 0 END) AS churned_count,
    ROUND(AVG(CASE WHEN churn = 'Yes' THEN 1.0 ELSE 0.0 END) * 100, 2) AS churn_rate_pct,
    ROUND(AVG(monthly_charges), 2) AS avg_monthly_bill
FROM customers
GROUP BY contract
ORDER BY churn_rate_pct DESC;


-- Q3: Revenue at Risk by Predicted Churn Probability (ML Model Scores)
SELECT 
    cs.risk_level,
    COUNT(*) AS customer_count,
    ROUND(SUM(cs.monthly_charges), 2) AS total_monthly_revenue,
    ROUND(SUM(cs.revenue_at_risk), 2) AS monthly_revenue_at_risk,
    ROUND(SUM(cs.clv_estimate), 2) AS total_clv_at_risk
FROM churn_scores cs
GROUP BY cs.risk_level
ORDER BY monthly_revenue_at_risk DESC;


-- Q4: Churn Rate by Internet Service Type & Tech Support Subscriptions
SELECT 
    internet_service,
    tech_support,
    COUNT(*) AS customer_count,
    SUM(CASE WHEN churn = 'Yes' THEN 1 ELSE 0 END) AS churned_count,
    ROUND(AVG(CASE WHEN churn = 'Yes' THEN 1.0 ELSE 0.0 END) * 100, 2) AS churn_rate_pct
FROM customers
GROUP BY internet_service, tech_support
ORDER BY churn_rate_pct DESC;


-- Q5: Average Tenure & Monthly Charges: Churned vs Retained
SELECT 
    churn,
    COUNT(*) AS customer_count,
    ROUND(AVG(tenure), 1) AS avg_tenure_months,
    ROUND(AVG(monthly_charges), 2) AS avg_monthly_charges,
    ROUND(AVG(total_charges), 2) AS avg_total_charges
FROM customers
GROUP BY churn;


-- Q6: Top 5 Missing Services Among Churned Customers
SELECT 
    'No Tech Support' AS missing_service, COUNT(*) AS churned_count FROM customers WHERE churn = 'Yes' AND tech_support = 'No'
UNION ALL
SELECT 'No Online Security', COUNT(*) FROM customers WHERE churn = 'Yes' AND online_security = 'No'
UNION ALL
SELECT 'No Online Backup', COUNT(*) FROM customers WHERE churn = 'Yes' AND online_backup = 'No'
UNION ALL
SELECT 'No Device Protection', COUNT(*) FROM customers WHERE churn = 'Yes' AND device_protection = 'No'
ORDER BY churned_count DESC;


-- Q7: Tenure Cohort Breakdown & Churn Risk Distribution
SELECT 
    CASE 
        WHEN tenure <= 12 THEN '0-12 Months (New)'
        WHEN tenure <= 24 THEN '13-24 Months (Early)'
        WHEN tenure <= 48 THEN '25-48 Months (Established)'
        ELSE '49+ Months (Loyal)'
    END AS tenure_cohort,
    COUNT(*) AS total_customers,
    SUM(CASE WHEN churn = 'Yes' THEN 1 ELSE 0 END) AS churned_count,
    ROUND(AVG(CASE WHEN churn = 'Yes' THEN 1.0 ELSE 0.0 END) * 100, 2) AS churn_rate_pct
FROM customers
GROUP BY 1
ORDER BY churn_rate_pct DESC;


-- Q8: Payment Method vs Churn & Paperless Billing Impact
SELECT 
    payment_method,
    paperless_billing,
    COUNT(*) AS customer_count,
    ROUND(AVG(CASE WHEN churn = 'Yes' THEN 1.0 ELSE 0.0 END) * 100, 2) AS churn_rate_pct
FROM customers
GROUP BY payment_method, paperless_billing
ORDER BY churn_rate_pct DESC;


-- Q9: Top 10 Highest Risk Active Customers (Intervention Queue)
SELECT 
    cs.customer_id,
    cs.contract,
    cs.tenure,
    cs.monthly_charges,
    cs.churn_probability,
    cs.revenue_at_risk,
    cs.clv_estimate
FROM churn_scores cs
WHERE cs.is_high_risk = 1
ORDER BY cs.churn_probability DESC, cs.monthly_charges DESC
LIMIT 10;


-- Q10: Senior Citizen Churn Rate & Add-on Adoption
SELECT 
    senior_citizen,
    COUNT(*) AS total_customers,
    ROUND(AVG(CASE WHEN churn = 'Yes' THEN 1.0 ELSE 0.0 END) * 100, 2) AS churn_rate_pct,
    ROUND(AVG(monthly_charges), 2) AS avg_monthly_bill
FROM customers
GROUP BY senior_citizen;


-- Q11: Service Bundling Depth (Number of Add-on Services vs Churn Rate)
SELECT 
    (
        (CASE WHEN phone_service = 'Yes' THEN 1 ELSE 0 END) +
        (CASE WHEN multiple_lines = 'Yes' THEN 1 ELSE 0 END) +
        (CASE WHEN online_security = 'Yes' THEN 1 ELSE 0 END) +
        (CASE WHEN online_backup = 'Yes' THEN 1 ELSE 0 END) +
        (CASE WHEN device_protection = 'Yes' THEN 1 ELSE 0 END) +
        (CASE WHEN tech_support = 'Yes' THEN 1 ELSE 0 END) +
        (CASE WHEN streaming_tv = 'Yes' THEN 1 ELSE 0 END) +
        (CASE WHEN streaming_movies = 'Yes' THEN 1 ELSE 0 END)
    ) AS total_services_count,
    COUNT(*) AS total_customers,
    ROUND(AVG(CASE WHEN churn = 'Yes' THEN 1.0 ELSE 0.0 END) * 100, 2) AS churn_rate_pct
FROM customers
GROUP BY 1
ORDER BY total_services_count ASC;


-- Q12: High Monthly Bill (> $80) Churn Rate by Contract Type
SELECT 
    contract,
    COUNT(*) AS high_bill_customers,
    ROUND(AVG(CASE WHEN churn = 'Yes' THEN 1.0 ELSE 0.0 END) * 100, 2) AS churn_rate_pct
FROM customers
WHERE monthly_charges > 80
GROUP BY contract
ORDER BY churn_rate_pct DESC;


-- Q13: Fiber Optic Internet Customer Segmentation & Security Risk
SELECT 
    online_security,
    tech_support,
    COUNT(*) AS total_fiber_customers,
    ROUND(AVG(CASE WHEN churn = 'Yes' THEN 1.0 ELSE 0.0 END) * 100, 2) AS churn_rate_pct
FROM customers
WHERE internet_service = 'Fiber optic'
GROUP BY online_security, tech_support
ORDER BY churn_rate_pct DESC;


-- Q14: Customer Lifetime Value (CLV) Loss by Payment Method
SELECT 
    payment_method,
    COUNT(*) AS total_churned,
    ROUND(SUM(monthly_charges * tenure), 2) AS cumulative_historical_loss,
    ROUND(AVG(monthly_charges * tenure), 2) AS avg_clv_per_churned_customer
FROM customers
WHERE churn = 'Yes'
GROUP BY payment_method
ORDER BY cumulative_historical_loss DESC;


-- Q15: High-Value Churn Risk Report (Scored Actives with Monthly Charges > $90)
SELECT 
    cs.customer_id,
    cs.contract,
    cs.tenure,
    cs.monthly_charges,
    cs.churn_probability,
    cs.clv_estimate
FROM churn_scores cs
WHERE cs.monthly_charges > 90.0 AND cs.churn_probability >= 0.50
ORDER BY cs.monthly_charges DESC, cs.churn_probability DESC;
