def compact_clusters(clusters):
    clusters = clusters or []

    return [
        {
            "cluster_id": c.get("cluster_id"),
            "warehouse": c.get("warehouse"),
            "area_focus": c.get("area_focus"),
            "order_count": c.get("order_count"),
        }
        for c in clusters
    ]


def format_chat_response(state):
    warehouse_plan = state.warehouse_plan or {}
    clusters = state.clusters or {}
    routes = state.routes or {}
    risks = state.risks or {}

    return {
        "run_id": state.runtime_logs[0]["run_id"] if state.runtime_logs else None,
        "session_id": state.session_id,
        "query": state.user_query,
        "city": state.city,
        "date": state.date,
        "selected_agents": state.selected_agents,
        "execution_plan": state.execution_plan,
        "steps": state.steps,
        "runtime_logs": state.runtime_logs,
        "summary": {
            "assigned_orders": warehouse_plan.get("assigned_orders", 0),
            "unassigned_orders": warehouse_plan.get("unassigned_orders", 0),
            "total_clusters": clusters.get("total_clusters", 0),
            "total_routes": routes.get("total_clusters_routed", 0),
            "total_risky_orders": risks.get("total_risky_orders", 0),
            "estimated_total_route_distance_km": routes.get(
                "estimated_total_route_distance_km", 0
            ),
        },
        "outputs": {
            "warehouse_plan": {
                "city": warehouse_plan.get("city"),
                "pending_orders_checked": warehouse_plan.get("pending_orders_checked", 0),
                "assigned_orders": warehouse_plan.get("assigned_orders", 0),
                "unassigned_orders": warehouse_plan.get("unassigned_orders", 0),
                "warehouse_wise_count": warehouse_plan.get("warehouse_wise_count", {}),
                "sample_assignments": warehouse_plan.get("sample_assignments", [])[:5],
                "sample_unassigned": warehouse_plan.get("sample_unassigned", [])[:5],
            },
            "clusters": {
                "total_clusters": clusters.get("total_clusters", 0),
                "radius_km": clusters.get("radius_km"),
                "sample_clusters": compact_clusters(
                    clusters.get("sample_clusters", [])[:5]
                ),
            },
            "routes": {
                "total_clusters_routed": routes.get("total_clusters_routed", 0),
                "estimated_total_route_distance_km": routes.get(
                    "estimated_total_route_distance_km", 0
                ),
                "sample_routes": routes.get("sample_routes", [])[:5],
            },
            "risks": {
                "total_orders_checked": risks.get("total_orders_checked", 0),
                "total_risky_orders": risks.get("total_risky_orders", 0),
                "risk_counts": risks.get("risk_counts", {}),
                "high_rto_areas": risks.get("high_rto_areas", [])[:5],
                "sample_risks": risks.get("sample_risks", [])[:5],
            },
        },
        "memo_file_path": state.memo_file_path,
        "final_memo": state.final_memo,
    }