import pandas as pd

from app.connectors.connector_manager import ConnectorManager
from app.utils.period_parser import filter_by_date


class LeakageDetectionService:
    def __init__(self):
        self.connector = ConnectorManager()

    def detect_leakage(self, period=None) -> dict:
        refunds = self.connector.load_csv("refunds.csv")
        payments = self.connector.load_csv("payments.csv")

        start_date = period.get("start_date") if period else None
        end_date = period.get("end_date") if period else None

        refunds = filter_by_date(refunds, "created_at", start_date, end_date)
        payments = filter_by_date(payments, "payment_date", start_date, end_date)

        refunds["refund_amount"] = pd.to_numeric(refunds["refund_amount"], errors="coerce").fillna(0)
        payments["amount"] = pd.to_numeric(payments["amount"], errors="coerce").fillna(0)

        total_refunds = float(refunds["refund_amount"].sum())
        total_payments = float(payments["amount"].sum())

        leakage_percentage = (
            (total_refunds / total_payments) * 100
            if total_payments > 0 else 0
        )

        high_refund_orders = refunds.sort_values(
            "refund_amount",
            ascending=False
        ).head(10)

        refund_reason_breakdown = (
            refunds.groupby("refund_reason")["refund_amount"]
            .sum()
            .reset_index()
            .sort_values("refund_amount", ascending=False)
            if len(refunds) else pd.DataFrame(columns=["refund_reason", "refund_amount"])
        )

        return {
            "period": period,
            "refund_rows": int(len(refunds)),
            "payment_rows": int(len(payments)),
            "total_refunds": round(total_refunds, 2),
            "total_payments": round(total_payments, 2),
            "leakage_percentage": round(leakage_percentage, 2),
            "refund_reason_breakdown": refund_reason_breakdown.to_dict(orient="records"),
            "high_risk_orders": high_refund_orders.to_dict(orient="records"),
            "citations": {
                "sources": [
                    "refunds.csv",
                    "payments.csv",
                ],
            },
        }