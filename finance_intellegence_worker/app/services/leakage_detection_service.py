import pandas as pd
from app.connectors.connector_manager import ConnectorManager


class LeakageDetectionService:
    def __init__(self):
        self.connector = ConnectorManager()

    def detect_leakage(self) -> dict:
        refunds = self.connector.load_csv("refunds.csv")
        payments = self.connector.load_csv("payments.csv")

        refunds["refund_amount"] = pd.to_numeric(
            refunds["refund_amount"],
            errors="coerce"
        ).fillna(0)

        payments["amount"] = pd.to_numeric(
            payments["amount"],
            errors="coerce"
        ).fillna(0)

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

        return {
            "total_refunds": round(total_refunds, 2),
            "total_payments": round(total_payments, 2),
            "leakage_percentage": round(leakage_percentage, 2),
            "high_risk_orders": high_refund_orders.to_dict(orient="records"),
            "citations": {
                "sources": ["refunds.csv", "payments.csv"],
            },
        }