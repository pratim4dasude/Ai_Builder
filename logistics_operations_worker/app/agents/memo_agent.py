import json

from app.agents.state import LogisticsAgentState
from app.llm.client import LLMClient
from app.llm.prompts import LOGISTICS_MEMO_SYSTEM_PROMPT


class MemoAgent:
    name = "MemoAgent"

    def run(self, state: LogisticsAgentState) -> LogisticsAgentState:
        warehouse_plan = state.warehouse_plan or {}
        clusters = state.clusters or {}
        routes = state.routes or {}
        risks = state.risks or {}

        warehouse_summary = {
            "city": warehouse_plan.get("city", state.city),
            "pending_orders_checked": warehouse_plan.get("pending_orders_checked", 0),
            "assigned_orders": warehouse_plan.get("assigned_orders", 0),
            "unassigned_orders": warehouse_plan.get("unassigned_orders", 0),
            "warehouse_wise_count": warehouse_plan.get("warehouse_wise_count", {}),
            "sample_assignments": warehouse_plan.get("sample_assignments", [])[:5],
        }

        cluster_summary = {
            "total_clusters": clusters.get("total_clusters", 0),
            "radius_km": clusters.get("radius_km"),
            "sample_clusters": clusters.get("sample_clusters", [])[:3],
        }

        route_summary = {
            "method": routes.get("method"),
            "total_clusters_routed": routes.get("total_clusters_routed", 0),
            "estimated_total_route_distance_km": routes.get(
                "estimated_total_route_distance_km", 0
            ),
            "sample_routes": routes.get("sample_routes", [])[:3],
        }

        risk_summary = {
            "summary": risks.get("summary", "Risk agent was not selected for this query."),
            "total_orders_checked": risks.get("total_orders_checked", 0),
            "total_risky_orders": risks.get("total_risky_orders", 0),
            "risk_counts": risks.get("risk_counts", {}),
            "high_rto_areas": risks.get("high_rto_areas", [])[:5],
            "sample_risks": risks.get("sample_risks", [])[:5],
        }

        def extract_citations(data):
            citations = []

            if isinstance(data, dict):
                for value in data.values():
                    citations.extend(extract_citations(value))

            elif isinstance(data, list):
                for item in data:
                    citations.extend(extract_citations(item))

            else:
                return []

            return citations

        grounded_citations = []

        grounded_citations.extend(
            extract_citations(
                warehouse_summary.get("sample_assignments", [])
            )
        )

        grounded_citations.extend(
            extract_citations(
                route_summary.get("sample_routes", [])
            )
        )

        grounded_citations.extend(
            extract_citations(
                risk_summary.get("sample_risks", [])
            )
        )

        cleaned_citations = []

        for item in grounded_citations:
            if isinstance(item, dict):
                if (
                        "table" in item
                        and "source" in item
                        and "source_row_id" in item
                ):
                    cleaned_citations.append(item)

        seen = set()
        unique_citations = []

        for c in cleaned_citations:
            key = (
                c["table"],
                c["source"],
                c["source_row_id"],
            )

            if key not in seen:
                seen.add(key)
                unique_citations.append(c)
        payload = {
            "user_query": state.user_query,
            "city": state.city,
            "date": state.date,
            "warehouse_summary": warehouse_summary,
            "cluster_summary": cluster_summary,
            "route_summary": route_summary,
            "risk_summary": risk_summary,
            "grounded_citations": unique_citations[:20],
        }

        user_prompt = f"""
Create a professional Daily Dispatch Decision Memo for the given city and date using only this grounded data. Do not write placeholders like [Insert Date].

Grounded data:
{json.dumps(payload, indent=2, default=str)}

Required memo sections:
1. Executive Summary
2. Warehouse Allocation
3. Delivery Clusters
4. Route Plan
5. Risk Flags
6. Recommended Actions
7. Citations / Evidence

Rules:
- Do not invent numbers.
- Keep it useful for an operations manager.
- Use ONLY citations present in grounded_citations.
- Never invent source names or row ids.
- If citations are unavailable for a section, explicitly say:
  "No grounded citation available."
"""

        try:
            llm = LLMClient()
            state.final_memo = llm.generate(
                system_prompt=LOGISTICS_MEMO_SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )

            message = "Generated final dispatch memo using LLM reasoning layer"

        except Exception as e:
            state.final_memo = f"""
Daily Dispatch Decision Memo

Executive Summary:
Processed {warehouse_summary.get("pending_orders_checked", 0)} pending orders for {warehouse_summary.get("city", state.city)}.
Assigned {warehouse_summary.get("assigned_orders", 0)} orders across warehouses, created {cluster_summary.get("total_clusters", 0)} delivery clusters, and generated routes for {route_summary.get("total_clusters_routed", 0)} clusters.

Warehouse Allocation:
{warehouse_summary}

Delivery Clusters:
{cluster_summary}

Route Plan:
{route_summary}

Risk Flags:
{risk_summary}

Recommended Actions:
Review warehouse allocation, process high-density clusters first, follow the suggested route sequence, and confirm risky COD/RTO orders before dispatch.

LLM fallback reason:
{str(e)}
"""

            message = "Generated fallback dispatch memo because LLM call failed"

        state.add_step(
            self.name,
            "completed",
            message,
        )

        return state