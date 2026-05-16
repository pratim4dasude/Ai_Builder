from typing import Dict, Any, List
import math


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    radius = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )

    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def cluster_assigned_orders(assignments: List[Dict[str, Any]], radius_km: float = 3.0):
    clusters = []
    used = set()

    for i, order in enumerate(assignments):
        if order["order_id"] in used:
            continue

        cluster_orders = [order]
        used.add(order["order_id"])

        for j, other in enumerate(assignments):
            if other["order_id"] in used:
                continue

            if order["selected_warehouse"] != other["selected_warehouse"]:
                continue

            if "latitude" not in order or "longitude" not in order:
                continue

            distance = haversine_km(
                float(order["latitude"]),
                float(order["longitude"]),
                float(other["latitude"]),
                float(other["longitude"]),
            )

            if distance <= radius_km:
                cluster_orders.append(other)
                used.add(other["order_id"])

        clusters.append({
            "cluster_id": f"CLUSTER_{len(clusters) + 1}",
            "warehouse": order["selected_warehouse"],
            "area_focus": list(set([o["area"] for o in cluster_orders])),
            "order_count": len(cluster_orders),
            "orders": cluster_orders,
        })

    return {
        "total_clusters": len(clusters),
        "radius_km": radius_km,
        "clusters": clusters,
        "sample_clusters": clusters[:20],
        "summary": f"Created {len(clusters)} delivery clusters using {radius_km} km radius",
    }