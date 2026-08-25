"""Generate a deterministic synthetic marketing campaign response dataset."""

from pathlib import Path

import numpy as np
import pandas as pd


SEED = 42
RECORD_COUNT = 12_000
OUTPUT = Path(__file__).resolve().parents[1] / "data" / "marketing_campaign_data.csv"


def generate_data(record_count: int = RECORD_COUNT, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    campaigns = pd.DataFrame(
        {
            "campaign_id": [f"CMP-{index:03d}" for index in range(1, 13)],
            "campaign_channel": [
                "Email", "Paid Search", "Social Media", "Display", "Affiliate", "SMS",
                "Email", "Paid Search", "Social Media", "Display", "Affiliate", "SMS",
            ],
            "campaign_date": pd.to_datetime(
                ["2025-01-15", "2025-02-10", "2025-03-05", "2025-03-28", "2025-04-18", "2025-05-12",
                 "2025-06-06", "2025-07-14", "2025-08-08", "2025-09-16", "2025-10-10", "2025-11-05"]
            ),
            "campaign_cost": [18500, 26000, 32000, 28000, 21000, 12000, 22000, 30000, 35000, 29000, 23000, 14000],
            "channel_ctr": [0.052, 0.041, 0.029, 0.018, 0.035, 0.075, 0.052, 0.041, 0.029, 0.018, 0.035, 0.075],
            "channel_cvr": [0.115, 0.095, 0.072, 0.045, 0.088, 0.125, 0.115, 0.095, 0.072, 0.045, 0.088, 0.125],
        }
    )
    customer_segments = rng.choice(["New", "Growing", "Loyal", "At Risk"], record_count, p=[0.34, 0.29, 0.22, 0.15])
    channel_index = rng.integers(0, len(campaigns), record_count)
    selected = campaigns.iloc[channel_index].reset_index(drop=True)
    segment_factor = pd.Series(customer_segments).map({"New": 0.86, "Growing": 1.05, "Loyal": 1.35, "At Risk": 0.72}).to_numpy()
    impressions = rng.poisson(8_000, record_count) + 1_000
    clicks = rng.binomial(impressions, np.clip(selected["channel_ctr"].to_numpy() * segment_factor, 0.005, 0.20))
    conversions = rng.binomial(clicks, np.clip(selected["channel_cvr"].to_numpy() * segment_factor, 0.01, 0.65))
    order_value = np.clip(rng.normal(118, 28, record_count) * segment_factor, 35, 320)
    previous_purchases = np.where(customer_segments == "New", 0, rng.poisson(np.where(customer_segments == "Loyal", 7, 2)))
    days_since_last_purchase = np.where(
        customer_segments == "New", rng.integers(90, 365, record_count), rng.integers(5, 220, record_count)
    )
    data = pd.DataFrame(
        {
            "customer_id": [f"CUST-{index:05d}" for index in rng.integers(1, 5_001, record_count)],
            "age": np.clip(rng.normal(39, 13, record_count).round(), 18, 78).astype(int),
            "gender": rng.choice(["Female", "Male", "Non-binary"], record_count, p=[0.49, 0.47, 0.04]),
            "city": rng.choice(["New York", "Chicago", "Los Angeles", "Houston", "Seattle", "Atlanta", "Denver"], record_count),
            "customer_segment": customer_segments,
            "campaign_id": selected["campaign_id"],
            "campaign_channel": selected["campaign_channel"],
            "campaign_date": selected["campaign_date"].dt.strftime("%Y-%m-%d"),
            "campaign_cost": selected["campaign_cost"].to_numpy() / 950 * rng.uniform(0.75, 1.25, record_count),
            "impressions": impressions,
            "clicks": clicks,
            "conversions": conversions,
            "revenue_generated": conversions * order_value,
            "previous_purchases": previous_purchases,
            "days_since_last_purchase": days_since_last_purchase,
        }
    )
    return data.round({"campaign_cost": 2, "revenue_generated": 2})


if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    generate_data().to_csv(OUTPUT, index=False)
    print(f"Wrote {RECORD_COUNT:,} rows to {OUTPUT}")
