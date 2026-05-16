from math import radians, sin, cos, sqrt, atan2
from typing import Dict, Any, List
import pandas as pd


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    radius = 6371

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )

    return radius * 2 * atan2(sqrt(a), sqrt(1 - a))


def assign_warehouses(
    orders: pd.DataFrame,
    warehouses: pd.DataFrame,
    inventory: pd.DataFrame,
    city: str = "Bangalore",
    limit: int = 100,
) -> Dict[str, Any]:

    city_orders = orders[
        (orders["city"].str.lower() == city.lower())
        & (orders["order_status"].str.lower().isin(["pending", "confirmed", "processing"]))
    ].copy()

    city_warehouses = warehouses[
        warehouses["city"].str.lower() == city.lower()
    ].copy()

    if limit:
        city_orders = city_orders.head(limit)

    assignments: List[Dict[str, Any]] = []
    unassigned: List[Dict[str, Any]] = []

    warehouse_load = {
        row["warehouse_id"]: int(row["current_load"])
        for _, row in city_warehouses.iterrows()
    }

    warehouse_capacity = {
        row["warehouse_id"]: int(row["capacity_per_day"])
        for _, row in city_warehouses.iterrows()
    }

    for _, order in city_orders.iterrows():
        eligible = []

        sku = order["sku"]
        qty = int(order["quantity"])

        for _, wh in city_warehouses.iterrows():
            wh_id = wh["warehouse_id"]

            stock_row = inventory[
                (inventory["warehouse_id"] == wh_id)
                & (inventory["sku"] == sku)
            ]

            if stock_row.empty:
                continue

            available_qty = int(stock_row.iloc[0]["available_qty"])
            reserved_qty = int(stock_row.iloc[0]["reserved_qty"])
            usable_stock = available_qty - reserved_qty

            if usable_stock < qty:
                continue

            if warehouse_load[wh_id] >= warehouse_capacity[wh_id]:
                continue

            distance = haversine_km(
                float(order["latitude"]),
                float(order["longitude"]),
                float(wh["latitude"]),
                float(wh["longitude"]),
            )

            eligible.append({
                "warehouse_id": wh_id,
                "warehouse_name": wh["warehouse_name"],
                "distance_km": round(distance, 2),
                "usable_stock": usable_stock,
                "capacity_remaining": warehouse_capacity[wh_id] - warehouse_load[wh_id],
                "warehouse_source_row_id": int(wh["source_row_id"]),
            })

        if not eligible:
            unassigned.append({
                "order_id": order["order_id"],
                "reason": "No warehouse found with stock and capacity",
                "source_row_id": int(order["source_row_id"]),
            })
            continue

        best = sorted(eligible, key=lambda x: x["distance_km"])[0]
        warehouse_load[best["warehouse_id"]] += qty

        assignments.append({
            "order_id": order["order_id"],
            "sku": sku,
            "quantity": qty,
            "area": order["area"],
            "pincode": str(order["pincode"]),
            "latitude": float(order["latitude"]),
            "longitude": float(order["longitude"]),
            "selected_warehouse": best["warehouse_name"],
            "warehouse_id": best["warehouse_id"],
            "distance_km": best["distance_km"],
            "reason": "Selected nearest warehouse with available stock and capacity",
            "citations": [
                {
                    "table": "orders",
                    "source": order["source"],
                    "source_row_id": int(order["source_row_id"]),
                },
                {
                    "table": "warehouses",
                    "source": "warehouses_csv",
                    "source_row_id": best["warehouse_source_row_id"],
                },
            ],
        })

    assignment_df = pd.DataFrame(assignments)

    warehouse_wise_count = (
        assignment_df["selected_warehouse"].value_counts().to_dict()
        if not assignment_df.empty
        else {}
    )

    return {
        "city": city,
        "pending_orders_checked": len(city_orders),
        "assigned_orders": len(assignments),
        "unassigned_orders": len(unassigned),
        "warehouse_wise_count": warehouse_wise_count,
        "assignments": assignments,
        "sample_assignments": assignments[:10],
        "sample_unassigned": unassigned[:10],
    }