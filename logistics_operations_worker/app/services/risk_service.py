from typing import Dict, Any, List
import pandas as pd


def detect_delivery_risks(
    orders: pd.DataFrame,
    shipments: pd.DataFrame,
    warehouse_plan: Dict[str, Any],
) -> Dict[str, Any]:

    assignments = warehouse_plan.get("assignments", [])

    if not assignments:
        return {
            "summary": "No assignments found for risk detection",
            "total_risky_orders": 0,
            "risk_counts": {},
            "sample_risks": [],
        }

    assigned_order_ids = [item["order_id"] for item in assignments]

    orders_df = orders[orders["order_id"].isin(assigned_order_ids)].copy()
    shipments_df = shipments[shipments["order_id"].isin(assigned_order_ids)].copy()

    risky_orders: List[Dict[str, Any]] = []

    rto_area_counts = (
        shipments_df[shipments_df["rto_status"].astype(str).str.lower() == "rto"]
        .groupby("area")
        .size()
        .to_dict()
    )

    high_rto_areas = {
        area for area, count in rto_area_counts.items()
        if count >= 2
    }

    for assignment in assignments:
        order_id = assignment["order_id"]

        order_rows = orders_df[orders_df["order_id"] == order_id]
        shipment_rows = shipments_df[shipments_df["order_id"] == order_id]

        if order_rows.empty:
            continue

        order = order_rows.iloc[0]
        risks = []

        payment_type = str(order.get("payment_type", "")).lower()
        area = str(order.get("area", ""))
        order_value = float(order.get("order_value", 0))

        if payment_type == "cod":
            risks.append("COD_ORDER")

        if payment_type == "cod" and order_value >= 3000:
            risks.append("HIGH_VALUE_COD")

        if area in high_rto_areas:
            risks.append("HIGH_RTO_AREA")

        if assignment.get("distance_km", 0) >= 10:
            risks.append("LONG_DISTANCE_FULFILLMENT")

        if not shipment_rows.empty:
            shipment = shipment_rows.iloc[0]

            attempts = int(shipment.get("delivery_attempts", 0))
            delivery_days = int(shipment.get("delivery_days", 0))
            shipment_status = str(shipment.get("shipment_status", "")).lower()
            rto_status = str(shipment.get("rto_status", "")).lower()

            if attempts >= 2:
                risks.append("MULTIPLE_DELIVERY_ATTEMPTS")

            if delivery_days >= 5:
                risks.append("SLA_DELAY_RISK")

            if rto_status == "rto":
                risks.append("PAST_RTO_SIGNAL")

            if shipment_status in ["failed", "undelivered"]:
                risks.append("FAILED_DELIVERY_SIGNAL")

        if risks:
            risky_orders.append({
                "order_id": order_id,
                "area": area,
                "pincode": str(order.get("pincode", "")),
                "payment_type": order.get("payment_type"),
                "order_value": order_value,
                "selected_warehouse": assignment.get("selected_warehouse"),
                "distance_km": assignment.get("distance_km"),
                "risk_flags": list(set(risks)),
                "recommended_action": get_recommended_action(risks),
                "citations": [
                    {
                        "table": "orders",
                        "source": order.get("source"),
                        "source_row_id": int(order.get("source_row_id")),
                    }
                ],
            })

    risk_counts = {}

    for item in risky_orders:
        for risk in item["risk_flags"]:
            risk_counts[risk] = risk_counts.get(risk, 0) + 1

    return {
        "summary": f"Detected {len(risky_orders)} risky orders out of {len(assignments)} assigned orders",
        "total_orders_checked": len(assignments),
        "total_risky_orders": len(risky_orders),
        "risk_counts": risk_counts,
        "high_rto_areas": list(high_rto_areas),
        "sample_risks": risky_orders[:10],
        "all_risks": risky_orders,
    }


def get_recommended_action(risks: List[str]) -> str:
    if "HIGH_VALUE_COD" in risks:
        return "Call customer before dispatch and confirm payment intent"

    if "HIGH_RTO_AREA" in risks:
        return "Prioritize reliable courier and verify address before shipping"

    if "SLA_DELAY_RISK" in risks:
        return "Escalate courier performance and monitor SLA breach"

    if "LONG_DISTANCE_FULFILLMENT" in risks:
        return "Review warehouse allocation or courier cost before dispatch"

    if "COD_ORDER" in risks:
        return "Send confirmation message before dispatch"

    return "Review manually before dispatch"