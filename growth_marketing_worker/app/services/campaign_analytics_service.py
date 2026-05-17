import pandas as pd


class CampaignAnalyticsService:
    def analyze_campaign_performance(self, campaigns_df: pd.DataFrame, products_df: pd.DataFrame) -> dict:
        if campaigns_df.empty:
            return {
                "status": "insufficient_data",
                "message": "No campaign data found",
                "top_campaigns": [],
                "top_channels": [],
                "product_campaign_summary": [],
                "citations": [],
            }

        df = campaigns_df.copy()

        df["ctr_percent"] = df.apply(
            lambda row: 0 if row["impressions"] == 0 else (row["clicks"] / row["impressions"]) * 100,
            axis=1,
        )

        df["cpc"] = df.apply(
            lambda row: 0 if row["clicks"] == 0 else row["spend"] / row["clicks"],
            axis=1,
        )

        df["conversion_rate_percent"] = df.apply(
            lambda row: 0 if row["clicks"] == 0 else (row["conversions"] / row["clicks"]) * 100,
            axis=1,
        )

        df["roas"] = df.apply(
            lambda row: 0 if row["spend"] == 0 else row["attributed_revenue"] / row["spend"],
            axis=1,
        )
        df["roas_capped"] = df["roas"].clip(0, 20)
        df["campaign_score"] = (
                df["ctr_percent"].clip(0, 20) * 0.30
                + df["conversion_rate_percent"].clip(0, 20) * 0.35
                + df["roas_capped"] * 0.25
                - df["cpc"].clip(0, 100) * 0.10
        )

        top_campaigns_df = df.sort_values(
            by=["campaign_score", "conversions"],
            ascending=False,
        ).head(10)

        channel_df = df.groupby("channel").agg(
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum"),
            spend=("spend", "sum"),
            conversions=("conversions", "sum"),
            attributed_revenue=("attributed_revenue", "sum"),
        ).reset_index()

        channel_df["ctr_percent"] = channel_df.apply(
            lambda row: 0 if row["impressions"] == 0 else (row["clicks"] / row["impressions"]) * 100,
            axis=1,
        )

        channel_df["conversion_rate_percent"] = channel_df.apply(
            lambda row: 0 if row["clicks"] == 0 else (row["conversions"] / row["clicks"]) * 100,
            axis=1,
        )

        channel_df["roas"] = channel_df.apply(
            lambda row: 0 if row["spend"] == 0 else row["attributed_revenue"] / row["spend"],
            axis=1,
        )

        channel_df["roas_capped"] = channel_df["roas"].clip(0, 20)

        channel_df["channel_score"] = (
                channel_df["ctr_percent"].clip(0, 20) * 0.30
                + channel_df["conversion_rate_percent"].clip(0, 20) * 0.35
                + channel_df["roas_capped"] * 0.25
        )

        channel_df = channel_df.sort_values(
            by=["channel_score", "conversions"],
            ascending=False,
        )

        product_df = df.groupby("product_id").agg(
            avg_ctr_percent=("ctr_percent", "mean"),
            avg_conversion_rate_percent=("conversion_rate_percent", "mean"),
            avg_roas=("roas", "mean"),
            total_conversions=("conversions", "sum"),
            total_spend=("spend", "sum"),
            total_attributed_revenue=("attributed_revenue", "sum"),
        ).reset_index()

        product_df["campaign_engagement_score"] = (
            product_df["avg_ctr_percent"] * 10
            + product_df["avg_conversion_rate_percent"] * 8
            + product_df["avg_roas"] * 5
        ).clip(0, 100)

        citations = []
        for campaign_id in top_campaigns_df["campaign_id"].tolist():
            source_rows = (
                df[df["campaign_id"] == campaign_id]["source_row_id"]
                .astype(str)
                .tolist()
            )

            citations.append({
                "metric": "campaign_performance",
                "campaign_id": campaign_id,
                "source": "campaign_csv",
                "source_row_ids": source_rows,
            })

        return {
            "status": "success",
            "top_campaigns": top_campaigns_df.to_dict(orient="records"),
            "top_channels": channel_df.head(10).to_dict(orient="records"),
            "product_campaign_summary": product_df.sort_values( by=["campaign_engagement_score", "total_conversions"], ascending=False, ).head(30).to_dict(orient="records"),
            "citations": citations,
        }