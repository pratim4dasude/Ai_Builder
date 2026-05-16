import json

from app.agents.state import LogisticsAgentState
from app.llm.client import LLMClient
from app.llm.prompts import LOGISTICS_MEMO_SYSTEM_PROMPT


class MemoAgent:
    name = "MemoAgent"

    def run(self, state: LogisticsAgentState) -> LogisticsAgentState:
        warehouse_summary = {
            "city": state.warehouse_plan.get("city"),
            "pending_orders_checked": state.warehouse_plan.get("pending_orders_checked"),
            "assigned_orders": state.warehouse_plan.get("assigned_orders"),
            "unassigned_orders": state.warehouse_plan.get("unassigned_orders"),
            "warehouse_wise_count": state.warehouse_plan.get("warehouse_wise_count"),
            "sample_assignments": state.warehouse_plan.get("sample_assignments", [])[:5],
        }

        cluster_summary = {
            "total_clusters": state.clusters.get("total_clusters"),
            "radius_km": state.clusters.get("radius_km"),
            "sample_clusters": state.clusters.get("sample_clusters", [])[:3],
        }

        route_summary = {
            "method": state.routes.get("method"),
            "total_clusters_routed": state.routes.get("total_clusters_routed"),
            "estimated_total_route_distance_km": state.routes.get(
                "estimated_total_route_distance_km"
            ),
            "sample_routes": state.routes.get("sample_routes", [])[:3],
        }

        risk_summary = {
            "summary": state.risks.get("summary"),
            "total_orders_checked": state.risks.get("total_orders_checked"),
            "total_risky_orders": state.risks.get("total_risky_orders"),
            "risk_counts": state.risks.get("risk_counts"),
            "high_rto_areas": state.risks.get("high_rto_areas", [])[:5],
            "sample_risks": state.risks.get("sample_risks", [])[:5],
        }

        payload = {
            "user_query": state.user_query,
            "city": state.city,
            "date": state.date,
            "warehouse_summary": warehouse_summary,
            "cluster_summary": cluster_summary,
            "route_summary": route_summary,
            "risk_summary": risk_summary,
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
- Mention source table and source_row_id where citations exist.
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
Processed {warehouse_summary["pending_orders_checked"]} pending orders for {warehouse_summary["city"]}.
Assigned {warehouse_summary["assigned_orders"]} orders across warehouses, created {cluster_summary["total_clusters"]} delivery clusters, and generated routes for {route_summary["total_clusters_routed"]} clusters.

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