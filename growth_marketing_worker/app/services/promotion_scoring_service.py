import pandas as pd


class PromotionScoringService:
    def calculate_promotion_scores(
        self,
        products_df: pd.DataFrame,
        sales_trends: dict,
        campaign_performance: dict,
    ) -> dict:
        if products_df.empty:
            return {
                "status": "insufficient_data",
                "message": "No product data found",
                "recommended_product": None,
                "ranked_products": [],
            }

        products = products_df.copy()

        sales_map = {
            item["product_id"]: item
            for item in sales_trends.get("top_products", [])
            if "product_id" in item
        }

        campaign_map = {
            item["product_id"]: item
            for item in campaign_performance.get("product_campaign_summary", [])
            if "product_id" in item
        }

        max_margin = products["margin_percent"].max()
        if max_margin == 0:
            max_margin = 1

        ranked_products = []

        for _, row in products.iterrows():
            product_id = row["product_id"]

            sales_item = sales_map.get(product_id, {})
            campaign_item = campaign_map.get(product_id, {})

            sales_growth = float(sales_item.get("quantity_growth_percent", 0))
            sales_growth_score = max(0, min(100, sales_growth))

            campaign_engagement_score = float(
                campaign_item.get("campaign_engagement_score", 0)
            )
            campaign_engagement_score = max(0, min(100, campaign_engagement_score))

            margin_score = (float(row["margin_percent"]) / max_margin) * 100
            margin_score = max(0, min(100, margin_score))

            conversion_score = float(
                campaign_item.get("avg_conversion_rate_percent", 0)
            ) * 10
            conversion_score = max(0, min(100, conversion_score))

            risk_score = 0

            if str(row.get("is_active", "true")).lower() == "false":
                risk_score += 50

            if float(row.get("inventory_count", 0)) < 10:
                risk_score += 30

            if float(row.get("refund_rate_percent", 0)) > 12:
                risk_score += 30

            if float(row.get("margin_percent", 0)) < 20:
                risk_score += 20

            if sales_growth <= 0:
                risk_score += 15

            risk_score = max(0, min(100, risk_score))

            final_score = (
                0.35 * sales_growth_score
                + 0.25 * campaign_engagement_score
                + 0.20 * margin_score
                + 0.10 * conversion_score
                - 0.10 * risk_score
            )

            ranked_products.append({
                "product_id": product_id,
                "sku": row.get("sku"),
                "product_name": row.get("product_name"),
                "category": row.get("category"),
                "subcategory": row.get("subcategory"),
                "target_segment": row.get("target_segment"),
                "customer_type": row.get("customer_type"),
                "price": float(row.get("price", 0)),
                "margin_percent": float(row.get("margin_percent", 0)),
                "inventory_count": int(row.get("inventory_count", 0)),
                "refund_rate_percent": float(row.get("refund_rate_percent", 0)),
                "sales_growth_score": round(sales_growth_score, 2),
                "campaign_engagement_score": round(campaign_engagement_score, 2),
                "margin_score": round(margin_score, 2),
                "conversion_score": round(conversion_score, 2),
                "risk_score": round(risk_score, 2),
                "promotion_readiness_score": round(final_score, 2),
            })

        ranked_products = sorted(
            ranked_products,
            key=lambda x: x["promotion_readiness_score"],
            reverse=True,
        )

        return {
            "status": "success",
            "formula": "0.35*sales_growth + 0.25*campaign_engagement + 0.20*margin + 0.10*conversion - 0.10*risk",
            "recommended_product": ranked_products[0] if ranked_products else None,
            "ranked_products": ranked_products[:20],
            "avoid_products": ranked_products[-10:],
        }