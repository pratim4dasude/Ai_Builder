from app.services.llm_service import LLMService


class ContentGenerationService:
    def __init__(self):
        self.llm_service = LLMService()

    def generate_content(
        self,
        recommended_product: dict,
        target_segment: dict,
        posting_time: dict,
        campaign_performance: dict,
    ) -> dict:
        if not recommended_product:
            return {
                "status": "insufficient_data",
                "message": "No recommended product found for content generation",
                "content_variants": {},
            }

        fallback = self._fallback_content(
            recommended_product=recommended_product,
            target_segment=target_segment,
            posting_time=posting_time,
            campaign_performance=campaign_performance,
        )

        system_prompt = """
You are a Growth Marketing Content Agent for a D2C ecommerce AI worker.

Your job:
- Generate channel-specific marketing content.
- Use only the provided product, segment, channel, and timing data.
- Do not invent numbers.
- Do not claim discounts unless discount data is provided.
- Keep copy concise, realistic, and brand-safe.
- Return valid JSON only.

Return JSON with this exact schema:
{
  "status": "success",
  "llm_used": true,
  "product_name": "...",
  "recommended_channel": "...",
  "recommended_posting_time": "...",
  "content_strategy": "...",
  "content_variants": {
    "instagram": "...",
    "facebook": "...",
    "whatsapp": "...",
    "email_subject": "...",
    "email_body": "...",
    "linkedin": "..."
  }
}
"""

        payload = {
            "recommended_product": recommended_product,
            "target_segment": target_segment,
            "posting_time": posting_time,
            "top_channels": campaign_performance.get("top_channels", [])[:3],
            "fallback_content": fallback,
        }

        return self.llm_service.generate_json(
            system_prompt=system_prompt,
            user_payload=payload,
            fallback=fallback,
        )

    def _fallback_content(
        self,
        recommended_product: dict,
        target_segment: dict,
        posting_time: dict,
        campaign_performance: dict,
    ) -> dict:
        product_name = recommended_product.get("product_name", "recommended product")
        segment = target_segment.get("target_segment", "target customers")
        city = target_segment.get("recommended_city", "Bangalore")
        channel = posting_time.get("best_channel") or self._best_channel(campaign_performance)
        time_window = posting_time.get("recommended_window", "19:00 - 21:00")

        return {
            "status": "success",
            "llm_used": False,
            "product_name": product_name,
            "recommended_channel": channel,
            "recommended_posting_time": time_window,
            "content_strategy": "Promote the selected product using comfort, demand, and everyday-style positioning.",
            "content_variants": {
                "instagram": f"{product_name} is built for everyday comfort and clean style. Perfect for {segment} in {city}. Drop goes live around {time_window}.",
                "facebook": f"Upgrade your everyday wardrobe with {product_name}. Strong demand, great value, and a style your customers are already responding to.",
                "whatsapp": f"Hey! {product_name} is trending now. Limited stock available for {city}. Shop before it sells out.",
                "email_subject": f"Trending now: {product_name}",
                "email_body": f"Hi, we picked {product_name} for you because it is showing strong demand, healthy campaign performance, and good promotion readiness. Explore it today.",
                "linkedin": f"{product_name} is showing strong growth and engagement signals across our commerce data. Recommended for a focused growth push this week.",
            },
        }

    def _best_channel(self, campaign_performance: dict) -> str:
        top_channels = campaign_performance.get("top_channels", [])

        if top_channels:
            return top_channels[0].get("channel", "Instagram")

        return "Instagram"