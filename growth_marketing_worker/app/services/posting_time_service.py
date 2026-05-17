import pandas as pd


class PostingTimeService:
    def find_best_posting_time(self, campaigns_df: pd.DataFrame, content_df: pd.DataFrame) -> dict:
        campaign_result = self._from_campaigns(campaigns_df)
        content_result = self._from_content(content_df)

        if campaign_result["status"] == "success":
            return campaign_result

        return content_result

    def _from_campaigns(self, campaigns_df: pd.DataFrame) -> dict:
        if campaigns_df.empty or "post_time" not in campaigns_df.columns:
            return {
                "status": "insufficient_data",
                "message": "No campaign post_time data found",
            }

        df = campaigns_df.copy()
        df["hour"] = df["post_time"].astype(str).str.slice(0, 2).astype(int)

        time_df = df.groupby(["channel", "hour"]).agg(
            clicks=("clicks", "sum"),
            conversions=("conversions", "sum"),
            spend=("spend", "sum"),
            attributed_revenue=("attributed_revenue", "sum"),
            campaigns=("campaign_id", "count"),
        ).reset_index()

        time_df["score"] = (
            time_df["conversions"] * 2
            + time_df["clicks"] * 0.05
            + time_df["attributed_revenue"] * 0.001
        )

        time_df = time_df.sort_values(by="score", ascending=False)

        best = time_df.iloc[0].to_dict()

        return {
            "status": "success",
            "source": "campaigns",
            "best_channel": best["channel"],
            "best_hour": int(best["hour"]),
            "recommended_window": f"{int(best['hour']):02d}:00 - {int(best['hour']) + 1:02d}:00",
            "reason": "Selected using historical campaign clicks, conversions, and attributed revenue",
            "top_time_windows": time_df.head(10).to_dict(orient="records"),
        }

    def _from_content(self, content_df: pd.DataFrame) -> dict:
        if content_df.empty or "published_datetime" not in content_df.columns:
            return {
                "status": "insufficient_data",
                "message": "No content calendar datetime data found",
            }

        df = content_df.copy()
        df["published_datetime"] = pd.to_datetime(df["published_datetime"], errors="coerce")
        df = df.dropna(subset=["published_datetime"])

        if df.empty:
            return {
                "status": "insufficient_data",
                "message": "No valid content published_datetime found",
            }

        df["hour"] = df["published_datetime"].dt.hour

        time_df = df.groupby(["channel", "hour"]).agg(
            engagements=("engagements", "sum"),
            clicks=("clicks", "sum"),
            conversions=("conversions", "sum"),
            content_count=("content_id", "count"),
        ).reset_index()

        time_df["score"] = (
            time_df["conversions"] * 2
            + time_df["clicks"] * 0.1
            + time_df["engagements"] * 0.01
        )

        time_df = time_df.sort_values(by="score", ascending=False)

        best = time_df.iloc[0].to_dict()

        return {
            "status": "success",
            "source": "content_calendar",
            "best_channel": best["channel"],
            "best_hour": int(best["hour"]),
            "recommended_window": f"{int(best['hour']):02d}:00 - {int(best['hour']) + 1:02d}:00",
            "reason": "Selected using historical content engagement, clicks, and conversions",
            "top_time_windows": time_df.head(10).to_dict(orient="records"),
        }