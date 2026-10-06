-- ============================================================================
-- 01_schema.sql — PostgreSQL Schema Setup for Customer Churn Analytics
-- ============================================================================

DROP TABLE IF EXISTS churn_scores CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

CREATE TABLE customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    gender VARCHAR(10),
    senior_citizen INT,
    partner VARCHAR(5),
    dependents VARCHAR(5),
    tenure INT,
    phone_service VARCHAR(5),
    multiple_lines VARCHAR(30),
    internet_service VARCHAR(30),
    online_security VARCHAR(30),
    online_backup VARCHAR(30),
    device_protection VARCHAR(30),
    tech_support VARCHAR(30),
    streaming_tv VARCHAR(30),
    streaming_movies VARCHAR(30),
    contract VARCHAR(30),
    paperless_billing VARCHAR(5),
    payment_method VARCHAR(50),
    monthly_charges NUMERIC(10, 2),
    total_charges NUMERIC(10, 2),
    churn VARCHAR(5)
);

CREATE TABLE churn_scores (
    customer_id VARCHAR(50) PRIMARY KEY REFERENCES customers(customer_id) ON DELETE CASCADE,
    tenure INT,
    contract VARCHAR(30),
    monthly_charges NUMERIC(10, 2),
    churn_probability NUMERIC(6, 4),
    risk_level VARCHAR(20),
    is_high_risk INT,
    revenue_at_risk NUMERIC(10, 2),
    clv_estimate NUMERIC(10, 2),
    scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_customers_contract ON customers(contract);
CREATE INDEX idx_customers_churn ON customers(churn);
CREATE INDEX idx_churn_scores_risk ON churn_scores(risk_level);
