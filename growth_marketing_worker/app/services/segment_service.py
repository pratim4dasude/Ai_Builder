import pandas as pd


class SegmentService:
    def recommend_target_segment(
        self,
        sales_df: pd.DataFrame,
        customers_df: pd.DataFrame,
        products_df: pd.DataFrame,
        recommended_product: dict,
    ) -> dict:
        if not recommended_product:
            return {
                "status": "insufficient_data",
                "message": "No recommended product found",
            }

        product_id = recommended_product.get("product_id")

        product_sales = sales_df[sales_df["product_id"] == product_id].copy()

        if product_sales.empty:
            product_row = products_df[products_df["product_id"] == product_id]
            target_segment = (
                product_row.iloc[0]["target_segment"]
                if not product_row.empty
                else "High-intent customers"
            )

            return {
                "status": "partial_success",
                "target_segment": target_segment,
                "recommended_city": "Bangalore",
                "recommended_customer_type": recommended_product.get("customer_type", "Returning"),
                "reason": "No sales rows found for recommended product, fallback used from product metadata",
            }

        city_df = product_sales.groupby("customer_city").agg(
            orders=("order_id", "count"),
            revenue=("net_revenue", "sum"),
            quantity=("quantity", "sum"),
        ).reset_index().sort_values(by="revenue", ascending=False)

        customer_type_df = product_sales.groupby("customer_type").agg(
            orders=("order_id", "count"),
            revenue=("net_revenue", "sum"),
            quantity=("quantity", "sum"),
        ).reset_index().sort_values(by="revenue", ascending=False)

        product_row = products_df[products_df["product_id"] == product_id]

        target_segment = (
            product_row.iloc[0]["target_segment"]
            if not product_row.empty
            else "High-intent customers"
        )

        return {
            "status": "success",
            "product_id": product_id,
            "target_segment": target_segment,
            "recommended_city": city_df.iloc[0]["customer_city"],
            "recommended_customer_type": customer_type_df.iloc[0]["customer_type"],
            "reason": "Selected using revenue and order concentration for the recommended product",
            "top_cities": city_df.head(5).to_dict(orient="records"),
            "top_customer_types": customer_type_df.to_dict(orient="records"),
        }