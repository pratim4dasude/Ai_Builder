class GrowthResponseFormatter:
    def format_chat_response(self, state):
        final_memo = state.final_memo or {}
        promotion_scores = state.promotion_scores or {}
        risk_analysis = state.risk_analysis or {}
        generated_content = state.generated_content or {}
        posting_time = state.posting_time or {}
        target_segment = state.target_segment or {}

        recommended_product = promotion_scores.get("recommended_product", {})
        risky_products = risk_analysis.get("risky_products", [])

        clean_risky_products = []
        for product in risky_products[:5]:
            clean_risky_products.append({
                "product_id": product.get("product_id"),
                "product_name": product.get("product_name"),
                "risk_score": product.get("risk_score"),
                "promotion_readiness_score": product.get("promotion_readiness_score"),
                "reason": self._build_risk_reason(product),
            })

        return {
            "worker": "Growth Marketing Worker",
            "query": state.user_query,
            "session_id": state.session_id,
            "selected_agents": state.selected_agents,
            "answer": {
                "decision": f"Promote {recommended_product.get('product_name')}",
                "product_to_promote": recommended_product.get("product_name"),
                "product_id": recommended_product.get("product_id"),
                "sku": recommended_product.get("sku"),
                "promotion_readiness_score": recommended_product.get("promotion_readiness_score"),
                "recommended_channel": final_memo.get("recommended_channel") or posting_time.get("best_channel"),
                "recommended_posting_time": final_memo.get("recommended_posting_time") or posting_time.get("recommended_window"),
                "target_segment": target_segment.get("target_segment"),
                "recommended_city": target_segment.get("recommended_city"),
                "recommended_customer_type": target_segment.get("recommended_customer_type"),
                "llm_used_for_content": generated_content.get("llm_used", False),
                "llm_used_for_memo": final_memo.get("llm_used", False),
                "executive_summary": final_memo.get("executive_summary"),
                "campaign_plan": final_memo.get("campaign_plan"),
                "risk_note": final_memo.get("risk_note"),
                "why": self._build_reasoning(recommended_product),
                "recommended_action": final_memo.get("recommended_action"),
                "suggested_content": generated_content.get("content_variants", {}),
                "products_to_avoid": clean_risky_products,
            },
            "citations": self._dedupe_citations(state.citations),
        }

    def format_stream_completed_response(self, state):
        return self.format_chat_response(state)

    def _build_reasoning(self, product):
        reasons = []

        if product.get("sales_growth_score", 0) >= 80:
            reasons.append("Strong recent sales growth signal")

        if product.get("campaign_engagement_score", 0) >= 80:
            reasons.append("Strong campaign engagement and conversion signal")

        if product.get("margin_score", 0) >= 60:
            reasons.append("Healthy margin for promotion")

        if product.get("risk_score", 100) <= 20:
            reasons.append("Low promotion risk based on inventory, refund, and margin checks")

        if product.get("inventory_count", 0) > 100:
            reasons.append("Enough inventory available for campaign push")

        if not reasons:
            reasons.append("Selected based on the highest Promotion Readiness Score")

        return reasons

    def _build_risk_reason(self, product):
        reasons = []

        if product.get("risk_score", 0) >= 80:
            reasons.append("high overall risk score")

        if product.get("margin_percent", 100) < 20:
            reasons.append("low margin")

        if product.get("inventory_count", 100) < 10:
            reasons.append("low inventory")

        if product.get("refund_rate_percent", 0) > 12:
            reasons.append("high refund rate")

        if product.get("campaign_engagement_score", 0) <= 10:
            reasons.append("weak campaign engagement")

        if product.get("sales_growth_score", 0) <= 0:
            reasons.append("weak or negative sales growth")

        return ", ".join(reasons) if reasons else "low promotion readiness"

    def _dedupe_citations(self, citations):
        seen = set()
        clean = []

        for citation in citations:
            key = (
                citation.get("metric"),
                citation.get("product_id"),
                citation.get("campaign_id"),
                citation.get("source"),
            )

            if key in seen:
                continue

            seen.add(key)
            clean.append(citation)

        return clean[:10]