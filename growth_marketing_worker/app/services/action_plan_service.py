class ActionPlanService:
    def generate_next_best_actions(
        self,
        query_intent: str,
        promotion_scores: dict,
        posting_time: dict,
        target_segment: dict,
        risk_analysis: dict,
        generated_content: dict,
        confidence: dict,
    ) -> list[dict]:
        recommended_product = promotion_scores.get("recommended_product", {})
        product_name = recommended_product.get("product_name", "recommended product")

        channel = posting_time.get("best_channel", "Instagram")
        window = posting_time.get("recommended_window", "19:00 - 20:00")
        city = target_segment.get("recommended_city", "Bangalore")
        segment = target_segment.get("target_segment", "target customers")

        actions = []

        if query_intent in ["promotion_recommendation", "content_generation", "segment_recommendation"]:
            actions.extend([
                {
                    "priority": "high",
                    "action": f"Launch {product_name} campaign on {channel}",
                    "reason": f"{product_name} has the highest promotion readiness score.",
                },
                {
                    "priority": "high",
                    "action": f"Schedule the main post during {window}",
                    "reason": "This time window has the strongest historical campaign performance.",
                },
                {
                    "priority": "medium",
                    "action": f"Target {segment} customers in {city}",
                    "reason": "This segment/location has the strongest product demand signal.",
                },
            ])

        if query_intent in ["risk_analysis", "promotion_recommendation"]:
            risky_products = risk_analysis.get("risky_products", [])[:3]

            for product in risky_products:
                actions.append({
                    "priority": "high" if product.get("risk_score", 0) >= 80 else "medium",
                    "action": f"Avoid promoting {product.get('product_name')}",
                    "reason": f"Risk score is {product.get('risk_score')} and promotion readiness score is {product.get('promotion_readiness_score')}.",
                })

        if query_intent in ["content_generation", "promotion_recommendation"]:
            if generated_content.get("content_variants"):
                actions.append({
                    "priority": "medium",
                    "action": "Use generated content variants across Instagram, WhatsApp, Email, and Facebook",
                    "reason": "The LLM content agent created channel-specific copy for execution.",
                })

        if confidence.get("level") == "low":
            actions.append({
                "priority": "high",
                "action": "Review data quality before launching campaign",
                "reason": "Confidence is low, so the recommendation needs more validation.",
            })
        else:
            actions.append({
                "priority": "medium",
                "action": "Review campaign performance after 24 hours",
                "reason": "This helps validate the recommendation and adjust spend quickly.",
            })

        return actions[:8]