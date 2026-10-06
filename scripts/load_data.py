"""Create the PostgreSQL schema and idempotently load customer records."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from src.config import DB_URI, RAW_CSV
from src.data import load_raw_data


def load_to_postgres(csv_path: str | Path = RAW_CSV, create_schema: bool = False) -> int:
    df = load_raw_data(csv_path).copy()
    df = df.rename(columns={
        "customerID": "customer_id", "SeniorCitizen": "senior_citizen",
        "PhoneService": "phone_service", "MultipleLines": "multiple_lines",
        "InternetService": "internet_service", "OnlineSecurity": "online_security",
        "OnlineBackup": "online_backup", "DeviceProtection": "device_protection",
        "TechSupport": "tech_support", "StreamingTV": "streaming_tv",
        "StreamingMovies": "streaming_movies", "Contract": "contract",
        "PaperlessBilling": "paperless_billing", "PaymentMethod": "payment_method",
        "MonthlyCharges": "monthly_charges", "TotalCharges": "total_charges",
        "Churn": "churn",
    })
    df["senior_citizen"] = df["senior_citizen"].map({"Yes": 1, "No": 0}).fillna(0).astype(int)
    engine = create_engine(DB_URI)
    with engine.begin() as conn:
        if create_schema:
            schema = (Path(__file__).resolve().parents[1] / "sql" / "01_schema.sql").read_text(encoding="utf-8")
            for statement in schema.split(";"):
                if statement.strip():
                    conn.exec_driver_sql(statement)
        df.to_sql("_staging_customers", con=conn, if_exists="replace", index=False)
        conn.execute(text("""
            INSERT INTO customers (
                customer_id, gender, senior_citizen, partner, dependents, tenure,
                phone_service, multiple_lines, internet_service, online_security,
                online_backup, device_protection, tech_support, streaming_tv,
                streaming_movies, contract, paperless_billing, payment_method,
                monthly_charges, total_charges, churn
            ) SELECT
                customer_id, gender, senior_citizen, partner, dependents, tenure,
                phone_service, multiple_lines, internet_service, online_security,
                online_backup, device_protection, tech_support, streaming_tv,
                streaming_movies, contract, paperless_billing, payment_method,
                monthly_charges, total_charges, churn
            FROM _staging_customers
            ON CONFLICT (customer_id) DO UPDATE SET
                gender = EXCLUDED.gender, senior_citizen = EXCLUDED.senior_citizen,
                partner = EXCLUDED.partner, dependents = EXCLUDED.dependents,
                tenure = EXCLUDED.tenure, phone_service = EXCLUDED.phone_service,
                multiple_lines = EXCLUDED.multiple_lines,
                internet_service = EXCLUDED.internet_service,
                online_security = EXCLUDED.online_security,
                online_backup = EXCLUDED.online_backup,
                device_protection = EXCLUDED.device_protection,
                tech_support = EXCLUDED.tech_support, streaming_tv = EXCLUDED.streaming_tv,
                streaming_movies = EXCLUDED.streaming_movies, contract = EXCLUDED.contract,
                paperless_billing = EXCLUDED.paperless_billing,
                payment_method = EXCLUDED.payment_method,
                monthly_charges = EXCLUDED.monthly_charges,
                total_charges = EXCLUDED.total_charges, churn = EXCLUDED.churn
        """))
        conn.exec_driver_sql("DROP TABLE _staging_customers")
    return len(df)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", default=str(RAW_CSV), help="Input Telco CSV")
    parser.add_argument("--create-schema", action="store_true", help="Create tables and indexes before loading")
    args = parser.parse_args()
    print(f"Loaded or updated {load_to_postgres(args.csv, args.create_schema):,} customer rows.")
