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
You are a senior Growth Marketing Content Agent for a D2C ecommerce AI worker.

Your job:
- Generate sharper, more natural, channel-specific marketing copy.
- Use only the provided product, segment, city, channel, and posting time.
- Do not invent numbers.
- Do not mention discounts unless discount data is provided.
- Do not say "limited stock" unless inventory is low.
- Do not copy fallback text directly.
- Keep the language premium, concise, and conversion-focused.
- Make Instagram more energetic.
- Make WhatsApp direct and personal.
- Make email clean and useful.
- Make LinkedIn business-friendly.
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
            "recommended_product": {
                "product_name": recommended_product.get("product_name"),
                "category": recommended_product.get("category"),
                "subcategory": recommended_product.get("subcategory"),
                "target_segment": recommended_product.get("target_segment"),
                "price": recommended_product.get("price"),
                "inventory_count": recommended_product.get("inventory_count"),
                "margin_percent": recommended_product.get("margin_percent"),
                "promotion_readiness_score": recommended_product.get("promotion_readiness_score"),
            },
            "target_segment": target_segment,
            "posting_time": posting_time,
            "top_channels": campaign_performance.get("top_channels", [])[:3],
            "fallback_content_style_reference": fallback,
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
        inventory_count = recommended_product.get("inventory_count", 0)

        stock_line = (
            f"Only {inventory_count} units available."
            if inventory_count and inventory_count < 50
            else "Available now."
        )

        return {
            "status": "success",
            "llm_used": False,
            "product_name": product_name,
            "recommended_channel": channel,
            "recommended_posting_time": time_window,
            "content_strategy": "Use everyday-style positioning with a clear product-first message.",
            "content_variants": {
                "instagram": f"{product_name} is made for everyday style and comfort. Perfect for {segment} in {city}. Catch it around {time_window}.",
                "facebook": f"Refresh your wardrobe with {product_name}. A strong pick for customers looking for comfort, style, and daily wear value.",
                "whatsapp": f"Hey! {product_name} is a top pick today. {stock_line} Best time to check it out: {time_window}.",
                "email_subject": f"Today’s top pick: {product_name}",
                "email_body": f"Hi, {product_name} is showing strong demand and good promotion readiness. It is a great fit for {segment} in {city}.",
                "linkedin": f"{product_name} is showing strong commerce signals across growth, engagement, and promotion readiness.",
            },
        }

    def _best_channel(self, campaign_performance: dict) -> str:
        top_channels = campaign_performance.get("top_channels", [])

        if top_channels:
            return top_channels[0].get("channel", "Instagram")

        return "Instagram"