import pandas as pd


class SalesAnalyticsService:
    def analyze_sales_trends(self, sales_df: pd.DataFrame, products_df: pd.DataFrame) -> dict:
        if sales_df.empty:
            return {
                "status": "insufficient_data",
                "message": "No sales data found",
                "top_products": [],
                "citations": [],
            }

        df = sales_df.copy()
        df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
        df = df.dropna(subset=["order_date"])

        latest_date = df["order_date"].max()
        current_start = latest_date - pd.Timedelta(days=7)
        previous_start = latest_date - pd.Timedelta(days=14)

        current_df = df[
            (df["order_date"] > current_start)
            & (df["order_date"] <= latest_date)
        ]

        previous_df = df[
            (df["order_date"] > previous_start)
            & (df["order_date"] <= current_start)
        ]

        current_summary = current_df.groupby("product_id").agg(
            current_quantity=("quantity", "sum"),
            current_revenue=("net_revenue", "sum"),
            current_orders=("order_id", "count"),
        ).reset_index()

        previous_summary = previous_df.groupby("product_id").agg(
            previous_quantity=("quantity", "sum"),
            previous_revenue=("net_revenue", "sum"),
            previous_orders=("order_id", "count"),
        ).reset_index()

        trend_df = current_summary.merge(
            previous_summary,
            on="product_id",
            how="left",
        ).fillna(0)

        trend_df["quantity_growth_percent"] = trend_df.apply(
            lambda row: 100.0
            if row["previous_quantity"] == 0 and row["current_quantity"] > 0
            else 0.0
            if row["previous_quantity"] == 0
            else ((row["current_quantity"] - row["previous_quantity"]) / row["previous_quantity"]) * 100,
            axis=1,
        )

        trend_df["revenue_growth_percent"] = trend_df.apply(
            lambda row: 100.0
            if row["previous_revenue"] == 0 and row["current_revenue"] > 0
            else 0.0
            if row["previous_revenue"] == 0
            else ((row["current_revenue"] - row["previous_revenue"]) / row["previous_revenue"]) * 100,
            axis=1,
        )

        product_cols = [
            "product_id",
            "sku",
            "product_name",
            "category",
            "subcategory",
            "margin_percent",
            "inventory_count",
            "refund_rate_percent",
            "rating",
            "is_active",
            "target_segment",
        ]

        available_product_cols = [col for col in product_cols if col in products_df.columns]

        trend_df = trend_df.merge(
            products_df[available_product_cols],
            on="product_id",
            how="left",
        )

        trend_df = trend_df.sort_values(
            by=["quantity_growth_percent", "current_revenue"],
            ascending=False,
        )

        top_products = trend_df.head(10).to_dict(orient="records")

        citations = []
        for product_id in trend_df.head(10)["product_id"].tolist():
            source_rows = (
                df[df["product_id"] == product_id]
                .sort_values("order_date", ascending=False)
                .head(10)["source_row_id"]
                .astype(str)
                .tolist()
            )

            citations.append({
                "metric": "sales_trend",
                "product_id": product_id,
                "source": "sales_csv",
                "source_row_ids": source_rows,
            })

        return {
            "status": "success",
            "latest_date": str(latest_date.date()),
            "analysis_window": "latest 7 days vs previous 7 days",
            "top_products": top_products,
            "citations": citations,
        }