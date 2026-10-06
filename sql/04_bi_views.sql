-- BI semantic layer: stable, one-row-per-customer views for Tableau and Power BI.
-- Apply after 01_schema.sql. Views update automatically as customers/scores change.

CREATE OR REPLACE VIEW v_customer_churn_analytics AS
SELECT
    c.customer_id,
    c.gender,
    c.senior_citizen,
    c.partner,
    c.dependents,
    c.tenure,
    CASE
        WHEN c.tenure <= 12 THEN '0-12 Months'
        WHEN c.tenure <= 24 THEN '13-24 Months'
        WHEN c.tenure <= 48 THEN '25-48 Months'
        ELSE '49+ Months'
    END AS tenure_band,
    c.phone_service,
    c.multiple_lines,
    c.internet_service,
    c.online_security,
    c.online_backup,
    c.device_protection,
    c.tech_support,
    c.streaming_tv,
    c.streaming_movies,
    c.contract,
    c.paperless_billing,
    c.payment_method,
    c.monthly_charges,
    c.total_charges,
    c.churn,
    CASE WHEN c.churn = 'Yes' THEN 1 ELSE 0 END AS churn_flag,
    s.churn_probability,
    s.risk_level,
    s.is_high_risk,
    s.revenue_at_risk,
    s.clv_estimate,
    s.clv_at_risk,
    s.scored_at,
    CASE WHEN s.customer_id IS NOT NULL THEN 1 ELSE 0 END AS has_model_score
FROM customers AS c
LEFT JOIN churn_scores AS s USING (customer_id);

CREATE OR REPLACE VIEW v_churn_bi_kpis AS
SELECT
    COUNT(*) AS total_customers,
    COUNT(*) FILTER (WHERE churn = 'Yes') AS churned_customers,
    ROUND(100.0 * COUNT(*) FILTER (WHERE churn = 'Yes') / NULLIF(COUNT(*), 0), 2) AS observed_churn_rate_pct,
    ROUND(SUM(monthly_charges) FILTER (WHERE churn = 'Yes'), 2) AS historical_churned_monthly_charges,
    COUNT(*) FILTER (WHERE has_model_score = 1) AS scored_active_customers,
    COUNT(*) FILTER (WHERE is_high_risk = 1) AS high_risk_scored_customers,
    ROUND(SUM(revenue_at_risk), 2) AS expected_monthly_revenue_at_risk,
    ROUND(SUM(clv_at_risk), 2) AS estimated_clv_at_risk,
    MAX(scored_at) AS latest_score_timestamp
FROM v_customer_churn_analytics;

CREATE OR REPLACE VIEW v_churn_contract_summary AS
SELECT
    contract,
    COUNT(*) AS total_customers,
    COUNT(*) FILTER (WHERE churn = 'Yes') AS churned_customers,
    ROUND(100.0 * COUNT(*) FILTER (WHERE churn = 'Yes') / NULLIF(COUNT(*), 0), 2) AS observed_churn_rate_pct,
    ROUND(AVG(monthly_charges), 2) AS avg_monthly_charges,
    COUNT(*) FILTER (WHERE has_model_score = 1) AS scored_active_customers,
    ROUND(SUM(revenue_at_risk), 2) AS expected_monthly_revenue_at_risk,
    ROUND(SUM(clv_at_risk), 2) AS estimated_clv_at_risk
FROM v_customer_churn_analytics
GROUP BY contract;
