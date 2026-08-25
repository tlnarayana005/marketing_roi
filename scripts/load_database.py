"""Load the generated CSV and analysis outputs into a normalized SQLite database."""

import sqlite3
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "marketing_roi.db"


def main() -> None:
    data = pd.read_csv(ROOT / "data" / "marketing_campaign_data.csv")
    rfm = pd.read_csv(ROOT / "outputs" / "rfm_customer_segments.csv")
    customers = data[["customer_id", "age", "gender", "city", "customer_segment", "previous_purchases", "days_since_last_purchase"]].drop_duplicates("customer_id")
    campaigns = data.groupby("campaign_id", as_index=False).agg(
        campaign_channel=("campaign_channel", "first"),
        campaign_date=("campaign_date", "first"),
        campaign_cost=("campaign_cost", "sum"),
    )
    responses = data[["customer_id", "campaign_id", "impressions", "clicks", "conversions", "revenue_generated"]]
    rfm = rfm.rename(columns={"rfm_segment": "rfm_segment"})
    with sqlite3.connect(DB_PATH) as connection:
        connection.executescript((ROOT / "sql" / "schema.sql").read_text())
        customers.to_sql("customers", connection, if_exists="append", index=False)
        campaigns.to_sql("campaigns", connection, if_exists="append", index=False)
        responses.to_sql("campaign_responses", connection, if_exists="append", index=False)
        rfm[["customer_id", "recency", "frequency", "monetary", "rfm_score", "rfm_segment"]].to_sql("rfm_scores", connection, if_exists="append", index=False)
    print(f"Loaded {len(responses):,} responses into {DB_PATH}")


if __name__ == "__main__":
    main()
