from typing import Dict, Any


def resolve_logistics_followup_query(query: str, previous_context: Dict[str, Any]) -> str:
    q = query.lower().strip()

    if not previous_context:
        return query

    last_main_task = previous_context.get("last_main_task")
    last_city = previous_context.get("last_city")
    last_warehouse_summary = previous_context.get("last_warehouse_summary")
    last_risk_summary = previous_context.get("last_risk_summary")
    last_route_summary = previous_context.get("last_route_summary")

    if "why" in q and "warehouse" in q:
        return f"Explain why the previous warehouse assignment was recommended. Previous warehouse summary: {last_warehouse_summary}"

    if "why" in q and last_main_task:
        return f"Explain why the previous logistics decision was made. Previous task: {last_main_task}"

    if "risky" in q or "risk" in q or "cod" in q or "rto" in q:
        return f"Show risky orders from the previous logistics plan. Previous risk summary: {last_risk_summary}"

    if "route" in q or "routing" in q or "delivery sequence" in q:
        return f"Explain the previous routing plan. Previous route summary: {last_route_summary}"

    if "cluster" in q or "group" in q:
        return "Explain the previous delivery clusters and why orders were grouped that way"

    if "memo" in q or "summary" in q or "action plan" in q:
        return (
            f"Create an operations action memo based on the previous logistics plan. "
            f"Task: {last_main_task}. City: {last_city}. "
            f"Warehouse summary: {last_warehouse_summary}. "
            f"Risk summary: {last_risk_summary}. "
            f"Route summary: {last_route_summary}."
        )

    if "what about" in q or "compare" in q:
        return f"{query}. Compare with previous logistics plan: {previous_context}"

    return query