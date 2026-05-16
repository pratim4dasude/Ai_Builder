import math
from typing import Dict, Any, List


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    radius = 6371

    dlat = math.radians(float(lat2) - float(lat1))
    dlon = math.radians(float(lon2) - float(lon1))

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(float(lat1)))
        * math.cos(math.radians(float(lat2)))
        * math.sin(dlon / 2) ** 2
    )

    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def nearest_neighbor_route(orders: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not orders:
        return {
            "route_sequence": [],
            "estimated_cluster_distance_km": 0,
        }

    remaining = orders.copy()
    route = []

    current = remaining.pop(0)
    route.append({
        "position": 1,
        "order_id": current["order_id"],
        "area": current["area"],
        "latitude": current["latitude"],
        "longitude": current["longitude"],
    })

    total_distance = 0.0
    position = 2

    while remaining:
        nearest_index = None
        nearest_distance = float("inf")

        for index, candidate in enumerate(remaining):
            distance = haversine_km(
                current["latitude"],
                current["longitude"],
                candidate["latitude"],
                candidate["longitude"],
            )

            if distance < nearest_distance:
                nearest_distance = distance
                nearest_index = index

        current = remaining.pop(nearest_index)
        total_distance += nearest_distance

        route.append({
            "position": position,
            "order_id": current["order_id"],
            "area": current["area"],
            "latitude": current["latitude"],
            "longitude": current["longitude"],
            "distance_from_previous_km": round(nearest_distance, 2),
        })

        position += 1

    return {
        "route_sequence": route,
        "estimated_cluster_distance_km": round(total_distance, 2),
    }


def generate_routes_for_clusters(clusters_data: Dict[str, Any]) -> Dict[str, Any]:
    clusters = clusters_data.get("clusters", [])

    routes = []

    for cluster in clusters:
        route_result = nearest_neighbor_route(cluster.get("orders", []))

        routes.append({
            "cluster_id": cluster["cluster_id"],
            "warehouse": cluster["warehouse"],
            "area_focus": cluster["area_focus"],
            "order_count": cluster["order_count"],
            "estimated_cluster_distance_km": route_result["estimated_cluster_distance_km"],
            "route_sequence": route_result["route_sequence"],
        })

    total_distance = sum(route["estimated_cluster_distance_km"] for route in routes)

    return {
        "summary": f"Generated routes for {len(routes)} clusters",
        "method": "Nearest-neighbor route heuristic",
        "total_clusters_routed": len(routes),
        "estimated_total_route_distance_km": round(total_distance, 2),
        "sample_routes": routes[:5],
        "routes": routes,
    }