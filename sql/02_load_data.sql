-- ============================================================================
-- 02_load_data.sql — COPY Data Ingestion Command for PostgreSQL
-- ============================================================================

COPY customers (
    customer_id, gender, senior_citizen, partner, dependents,
    tenure, phone_service, multiple_lines, internet_service,
    online_security, online_backup, device_protection, tech_support,
    streaming_tv, streaming_movies, contract, paperless_billing,
    payment_method, monthly_charges, total_charges, churn
)
FROM '/path/to/data/telco_churn.csv'
WITH (FORMAT csv, HEADER true, DELIMITER ',');
