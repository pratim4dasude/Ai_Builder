class ConfidenceService:
    def calculate_confidence(
        self,
        sales_trends: dict,
        campaign_performance: dict,
        promotion_scores: dict,
        posting_time: dict,
        target_segment: dict,
        risk_analysis: dict,
    ) -> dict:
        recommended_product = promotion_scores.get("recommended_product", {})

        if not recommended_product:
            return {
                "score": 0.0,
                "level": "low",
                "reason": "No recommended product was available for confidence scoring.",
                "signals": [],
            }

        score = 0
        signals = []

        sales_growth_score = recommended_product.get("sales_growth_score", 0)
        campaign_engagement_score = recommended_product.get("campaign_engagement_score", 0)
        margin_score = recommended_product.get("margin_score", 0)
        conversion_score = recommended_product.get("conversion_score", 0)
        risk_score = recommended_product.get("risk_score", 100)
        inventory_count = recommended_product.get("inventory_count", 0)
        refund_rate_percent = recommended_product.get("refund_rate_percent", 100)

        if sales_growth_score >= 80:
            score += 20
            signals.append("Strong sales growth signal")

        if campaign_engagement_score >= 70:
            score += 20
            signals.append("Strong campaign engagement signal")

        if margin_score >= 60:
            score += 15
            signals.append("Healthy margin signal")

        if conversion_score >= 40:
            score += 10
            signals.append("Good conversion signal")

        if risk_score <= 20:
            score += 15
            signals.append("Low risk signal")

        if inventory_count >= 100:
            score += 10
            signals.append("Enough inventory available")

        if refund_rate_percent <= 5:
            score += 5
            signals.append("Low refund rate")

        if posting_time.get("status") == "success":
            score += 3
            signals.append("Posting time recommendation available")

        if target_segment.get("status") == "success":
            score += 2
            signals.append("Target segment recommendation available")

        score = min(score, 95)

        if score >= 80:
            level = "high"
        elif score >= 55:
            level = "medium"
        else:
            level = "low"

        return {
            "score": round(score / 100, 2),
            "percentage": score,
            "level": level,
            "reason": self._build_reason(level, recommended_product),
            "signals": signals,
        }

    def _build_reason(self, level: str, product: dict) -> str:
        product_name = product.get("product_name", "recommended product")

        if level == "high":
            return f"High confidence because {product_name} has strong sales, campaign, margin, inventory, and low-risk signals."

        if level == "medium":
            return f"Medium confidence because {product_name} has useful promotion signals, but some supporting signals are weaker."

        return f"Low confidence because {product_name} does not have enough strong supporting signals across sales, campaigns, margin, and risk."