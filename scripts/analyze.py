"""Clean, analyze, and export marketing performance tables and charts."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "marketing_campaign_data.csv"
OUTPUT_DIR = ROOT / "outputs"


def load_and_clean(path: Path = DATA_PATH) -> pd.DataFrame:
    data = pd.read_csv(path, parse_dates=["campaign_date"])
    numeric_columns = ["age", "campaign_cost", "impressions", "clicks", "conversions", "revenue_generated", "previous_purchases", "days_since_last_purchase"]
    data[numeric_columns] = data[numeric_columns].apply(pd.to_numeric, errors="coerce")
    data = data.drop_duplicates().dropna(subset=["customer_id", "campaign_id", "campaign_date"])
    data = data[(data["impressions"] > 0) & (data["campaign_cost"] >= 0)]
    data["click_through_rate"] = data["clicks"] / data["impressions"]
    data["conversion_rate"] = data["conversions"] / data["clicks"].where(data["clicks"] > 0)
    data["conversion_rate"] = data["conversion_rate"].fillna(0)
    return data


def summarize(data: pd.DataFrame) -> dict[str, pd.DataFrame]:
    def aggregate(group_columns: list[str]) -> pd.DataFrame:
        result = data.groupby(group_columns, as_index=False).agg(
            customers=("customer_id", "nunique"), campaigns=("campaign_id", "nunique"),
            spend=("campaign_cost", "sum"), impressions=("impressions", "sum"), clicks=("clicks", "sum"),
            conversions=("conversions", "sum"), revenue=("revenue_generated", "sum"),
        )
        result["ctr"] = result["clicks"] / result["impressions"]
        result["conversion_rate"] = result["conversions"] / result["clicks"].where(result["clicks"] > 0)
        result["cac"] = result["spend"] / result["conversions"].where(result["conversions"] > 0)
        result["roi"] = (result["revenue"] - result["spend"]) / result["spend"].where(result["spend"] > 0)
        result["revenue_per_customer"] = result["revenue"] / result["customers"].where(result["customers"] > 0)
        result["aov"] = result["revenue"] / result["conversions"].where(result["conversions"] > 0)
        return result.fillna(0)

    return {
        "campaign_performance": aggregate(["campaign_id", "campaign_channel", "campaign_date"]),
        "channel_performance": aggregate(["campaign_channel"]),
        "segment_performance": aggregate(["customer_segment"]),
        "monthly_trends": aggregate([data["campaign_date"].dt.to_period("M").astype(str).rename("month")]),
    }


def build_rfm(data: pd.DataFrame) -> pd.DataFrame:
    reference_date = data["campaign_date"].max() + pd.Timedelta(days=1)
    rfm = data.groupby("customer_id").agg(
        recency=("campaign_date", lambda dates: (reference_date - dates.max()).days),
        frequency=("campaign_id", "nunique"), monetary=("revenue_generated", "sum"),
    ).reset_index()
    for column in ["recency", "frequency", "monetary"]:
        rfm[f"{column}_score"] = pd.qcut(rfm[column].rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)
    rfm["recency_score"] = 5 - rfm["recency_score"]
    rfm["rfm_score"] = rfm[["recency_score", "frequency_score", "monetary_score"]].sum(axis=1)
    rfm["rfm_segment"] = pd.cut(
        rfm["rfm_score"], bins=[0, 5, 8, 10, 12], labels=["At Risk", "Occasional", "Growing", "Champions"]
    ).astype(str)
    return rfm


def create_charts(tables: dict[str, pd.DataFrame]) -> None:
    sns.set_theme(style="whitegrid", palette="deep")
    channel = tables["channel_performance"].sort_values("roi", ascending=False)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    sns.barplot(data=channel, x="roi", y="campaign_channel", ax=axes[0])
    axes[0].set(title="ROI by channel", xlabel="ROI", ylabel="")
    sns.barplot(data=channel, x="conversion_rate", y="campaign_channel", ax=axes[1])
    axes[1].set(title="Conversion rate by channel", xlabel="Conversion rate", ylabel="")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "channel_performance.png", dpi=160)
    plt.close(fig)

    monthly = tables["monthly_trends"]
    fig, ax = plt.subplots(figsize=(11, 5))
    sns.lineplot(data=monthly, x="month", y="revenue", marker="o", label="Revenue", ax=ax)
    sns.lineplot(data=monthly, x="month", y="spend", marker="o", label="Spend", ax=ax)
    ax.set(title="Monthly revenue and spend", xlabel="Month", ylabel="Amount ($)")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "monthly_trends.png", dpi=160)
    plt.close(fig)


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    data = load_and_clean()
    tables = summarize(data)
    rfm = build_rfm(data)
    kpis = pd.DataFrame([{
        "total_spend": data["campaign_cost"].sum(), "total_revenue": data["revenue_generated"].sum(),
        "overall_roi": (data["revenue_generated"].sum() - data["campaign_cost"].sum()) / data["campaign_cost"].sum(),
        "conversion_rate": data["conversions"].sum() / data["clicks"].sum(),
        "cac": data["campaign_cost"].sum() / data["conversions"].sum(),
        "revenue_per_customer": data["revenue_generated"].sum() / data["customer_id"].nunique(),
        "aov": data["revenue_generated"].sum() / data["conversions"].sum(),
    }])
    data.to_csv(OUTPUT_DIR / "cleaned_campaign_data.csv", index=False)
    kpis.to_csv(OUTPUT_DIR / "kpis.csv", index=False)
    for name, table in tables.items():
        table.to_csv(OUTPUT_DIR / f"{name}.csv", index=False)
    rfm.to_csv(OUTPUT_DIR / "rfm_customer_segments.csv", index=False)
    create_charts(tables)
    print(kpis.to_string(index=False))


if __name__ == "__main__":
    main()
