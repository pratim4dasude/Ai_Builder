from typing import Dict, Any


def resolve_finance_followup_query(query: str, previous_context: Dict[str, Any]) -> str:
    q = query.lower().strip()

    if not previous_context:
        return query

    last_intent = previous_context.get("last_intent")
    last_period = previous_context.get("last_period")
    last_main_issue = previous_context.get("last_main_issue")
    last_focus_area = previous_context.get("last_focus_area")

    if "why" in q and last_main_issue:
        return f"Explain why this finance issue is happening: {last_main_issue}"

    if "why" in q and last_intent:
        return f"Explain the reason behind the previous finance analysis. Previous intent: {last_intent}"

    if "memo" in q or "summary" in q or "action plan" in q:
        return (
            f"Create a finance action memo based on the previous analysis. "
            f"Focus area: {last_focus_area}. Main issue: {last_main_issue}. Period: {last_period}."
        )

    if "what about invoices" in q or "invoice" in q:
        return "Analyze invoice risks based on the previous finance context"

    if "what about leakage" in q or "leakage" in q:
        return "Analyze revenue leakage based on the previous finance context"

    if "what about margin" in q or "margin" in q:
        return "Analyze margin performance based on the previous finance context"

    if "compare" in q:
        return f"{query}. Compare with previous finance analysis: {previous_context}"

    return query