CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE analytics.churn_predictions (
    user_account_id TEXT PRIMARY KEY,
    country TEXT,
    industry_type TEXT,
    registration_plan_code TEXT,
    customer_tenure_days INTEGER,
    is_churned_historical INTEGER,
    calibrated_churn_probability DOUBLE PRECISION,
    monthly_arpu DOUBLE PRECISION,
    projected_ltv DOUBLE PRECISION,
    currency TEXT,
    allocated_operational_tier TEXT,
    primary_frustration_driver_vector TEXT,
    prediction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
