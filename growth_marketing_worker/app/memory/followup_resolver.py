from typing import Dict, Any


def resolve_followup_query(query: str, previous_context: Dict[str, Any]) -> str:
    q = query.lower().strip()

    if not previous_context:
        return query

    last_product = previous_context.get("last_product_name")
    last_channel = previous_context.get("last_channel")
    last_segment = previous_context.get("last_segment")
    last_city = previous_context.get("last_city")
    last_posting_time = previous_context.get("last_posting_time")

    if ("why" in q or "reason" in q) and last_product:
        return f"Explain why {last_product} was recommended for promotion"

    if ("make content" in q or "caption" in q or "post" in q) and last_product:
        channel_text = f" for {last_channel}" if last_channel else ""
        return f"Create marketing content for {last_product}{channel_text}"

    if ("memo" in q or "summary" in q or "action plan" in q) and last_product:
        return (
            f"Create a marketing action memo for {last_product}. "
            f"Channel: {last_channel}. Segment: {last_segment}. "
            f"City: {last_city}. Posting time: {last_posting_time}."
        )

    if ("what about" in q or "compare" in q) and last_product:
        return f"{query}. Compare it with previous recommended product: {last_product}"

    if ("only instagram" in q or "instagram only" in q) and last_product:
        return f"Create Instagram-only campaign content for {last_product}"

    return query