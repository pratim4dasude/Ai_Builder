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
You are a Growth Marketing Memo Agent for an AI Employee Platform.

Your job:
- Create a concise executive marketing action memo.
- Use only the deterministic analytics provided.
- Do not invent numbers.
- Do not change the recommended product, score, channel, posting time, or segment.
- Explain the decision clearly.
- Mention risk/avoidance briefly if available.
- Keep tone practical and business-friendly.
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
    "message_angle": "..."
  },
  "suggested_content": {},
  "risk_note": "...",
  "citations": []
}
"""

        payload = {
            "query": query,
            "sales_trends": {
                "latest_date": sales_trends.get("latest_date"),
                "analysis_window": sales_trends.get("analysis_window"),
                "top_products": sales_trends.get("top_products", [])[:3],
            },
            "campaign_performance": {
                "top_channels": campaign_performance.get("top_channels", [])[:3],
                "top_campaigns": campaign_performance.get("top_campaigns", [])[:3],
            },
            "promotion_scores": {
                "recommended_product": promotion_scores.get("recommended_product"),
                "avoid_products": promotion_scores.get("avoid_products", [])[:3],
                "formula": promotion_scores.get("formula"),
            },
            "posting_time": posting_time,
            "target_segment": target_segment,
            "generated_content": generated_content,
            "citations": citations[:8],
            "fallback_memo": fallback,
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
            "executive_summary": f"Promote {product_name} because it has the strongest combined signal across sales growth, campaign engagement, margin, conversion, and risk.",
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
            },
            "suggested_content": generated_content.get("content_variants", {}),
            "risk_note": "Avoid low-scoring products with weak sales, low margin, high refund rate, low inventory, or poor campaign engagement.",
            "citations": citations,
        }