from app.services.llm_service import LLMService


class MemoService:
    def __init__(self):
        self.llm_service = LLMService()

    def create_growth_action_memo(
        self,
        query: str,
        sales_trends: dict,
        campaign_performance: dict,
        promotion_scores: dict,
        posting_time: dict,
        target_segment: dict,
        generated_content: dict,
        citations: list,
    ) -> dict:
        fallback = self._fallback_memo(
            query=query,
            sales_trends=sales_trends,
            campaign_performance=campaign_performance,
            promotion_scores=promotion_scores,
            posting_time=posting_time,
            target_segment=target_segment,
            generated_content=generated_content,
            citations=citations,
        )

        system_prompt = """
You are a senior Growth Marketing Strategy Agent for an AI Employee Platform.

Your job:
- Write a concise business action memo.
- Keep all numbers exactly as provided.
- Do not invent metrics.
- Do not change the selected product, score, channel, time, city, or segment.
- Explain the decision in practical business language.
- Mention why this should be promoted now.
- Mention what to avoid.
- Keep it suitable for a D2C founder or growth team.
- Return valid JSON only.

Return JSON with this exact schema:
{
  "status": "success",
  "llm_used": true,
  "title": "Growth Action Memo",
  "query": "...",
  "product_to_promote": "...",
  "product_id": "...",
  "sku": "...",
  "promotion_readiness_score": 0,
  "recommended_channel": "...",
  "recommended_posting_time": "...",
  "target_segment": "...",
  "recommended_city": "...",
  "recommended_customer_type": "...",
  "executive_summary": "...",
  "decision_reasoning": ["...", "..."],
  "recommended_action": "...",
  "campaign_plan": {
    "primary_channel": "...",
    "posting_window": "...",
    "audience": "...",
    "message_angle": "...",
    "execution_steps": ["...", "...", "..."]
  },
  "suggested_content": {},
  "risk_note": "...",
  "citations": []
}
"""

        recommended_product = promotion_scores.get("recommended_product", {})

        payload = {
            "query": query,
            "fixed_decision": {
                "product_to_promote": recommended_product.get("product_name"),
                "product_id": recommended_product.get("product_id"),
                "sku": recommended_product.get("sku"),
                "promotion_readiness_score": recommended_product.get("promotion_readiness_score"),
                "recommended_channel": posting_time.get("best_channel"),
                "recommended_posting_time": posting_time.get("recommended_window"),
                "target_segment": target_segment.get("target_segment"),
                "recommended_city": target_segment.get("recommended_city"),
                "recommended_customer_type": target_segment.get("recommended_customer_type"),
            },
            "supporting_signals": {
                "sales_growth_score": recommended_product.get("sales_growth_score"),
                "campaign_engagement_score": recommended_product.get("campaign_engagement_score"),
                "margin_score": recommended_product.get("margin_score"),
                "conversion_score": recommended_product.get("conversion_score"),
                "risk_score": recommended_product.get("risk_score"),
                "inventory_count": recommended_product.get("inventory_count"),
                "refund_rate_percent": recommended_product.get("refund_rate_percent"),
            },
            "top_channels": campaign_performance.get("top_channels", [])[:3],
            "avoid_products": promotion_scores.get("avoid_products", [])[:3],
            "generated_content": generated_content,
            "citations": citations[:8],
            "fallback_memo_style_reference": fallback,
        }

        return self.llm_service.generate_json(
            system_prompt=system_prompt,
            user_payload=payload,
            fallback=fallback,
        )

    def _fallback_memo(
        self,
        query: str,
        sales_trends: dict,
        campaign_performance: dict,
        promotion_scores: dict,
        posting_time: dict,
        target_segment: dict,
        generated_content: dict,
        citations: list,
    ) -> dict:
        recommended_product = promotion_scores.get("recommended_product", {})
        top_channels = campaign_performance.get("top_channels", [])

        best_channel = (
            posting_time.get("best_channel")
            or top_channels[0].get("channel")
            if top_channels
            else "Instagram"
        )

        product_name = recommended_product.get("product_name")
        time_window = posting_time.get("recommended_window")

        return {
            "status": "success",
            "llm_used": False,
            "title": "Growth Action Memo",
            "query": query,
            "product_to_promote": product_name,
            "product_id": recommended_product.get("product_id"),
            "sku": recommended_product.get("sku"),
            "promotion_readiness_score": recommended_product.get("promotion_readiness_score"),
            "recommended_channel": best_channel,
            "recommended_posting_time": time_window,
            "target_segment": target_segment.get("target_segment"),
            "recommended_city": target_segment.get("recommended_city"),
            "recommended_customer_type": target_segment.get("recommended_customer_type"),
            "executive_summary": f"{product_name} is the best product to promote now because it combines strong growth, strong campaign engagement, healthy margin, and low risk.",
            "decision_reasoning": [
                f"Sales growth score is {recommended_product.get('sales_growth_score')}.",
                f"Campaign engagement score is {recommended_product.get('campaign_engagement_score')}.",
                f"Margin score is {recommended_product.get('margin_score')}.",
                f"Risk score is {recommended_product.get('risk_score')}.",
                "The recommendation uses deterministic analytics, not LLM-generated numbers.",
            ],
            "recommended_action": f"Promote {product_name} on {best_channel} during {time_window}.",
            "campaign_plan": {
                "primary_channel": best_channel,
                "posting_window": time_window,
                "audience": target_segment.get("target_segment"),
                "message_angle": "everyday comfort, demand, and clean style",
                "execution_steps": [
                    "Run the primary post during the recommended time window.",
                    "Use the generated content variants across Instagram, WhatsApp, and Email.",
                    "Avoid low-scoring products until margin, refund, or inventory issues improve.",
                ],
            },
            "suggested_content": generated_content.get("content_variants", {}),
            "risk_note": "Avoid low-scoring products with weak sales, low margin, high refund rate, low inventory, or poor campaign engagement.",
            "citations": citations,
        }