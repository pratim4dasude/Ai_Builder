import pandas as pd

from app.connectors.connector_manager import ConnectorManager


class MarginRefundService:
    def __init__(self):
        self.connector = ConnectorManager()

    def analyze_margin(self) -> dict:
        orders = self.connector.load_csv("orders.csv")
        expenses = self.connector.load_csv("expenses.csv")
        refunds = self.connector.load_csv("refunds.csv")

        orders["net_amount"] = pd.to_numeric(
            orders["net_amount"],
            errors="coerce"
        ).fillna(0)

        expenses["amount"] = pd.to_numeric(
            expenses["amount"],
            errors="coerce"
        ).fillna(0)

        refunds["refund_amount"] = pd.to_numeric(
            refunds["refund_amount"],
            errors="coerce"
        ).fillna(0)

        total_revenue = float(orders["net_amount"].sum())
        total_expenses = float(expenses["amount"].sum())
        total_refunds = float(refunds["refund_amount"].sum())

        gross_margin = total_revenue - total_expenses - total_refunds

        margin_percentage = (
            (gross_margin / total_revenue) * 100
            if total_revenue > 0 else 0
        )

        expense_by_category = (
            expenses.groupby("category")["amount"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )

        refund_by_reason = (
            refunds.groupby("refund_reason")["refund_amount"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )

        high_expense_threshold = expenses["amount"].quantile(0.95)

        unusual_expenses = expenses[
            expenses["amount"] >= high_expense_threshold
        ].sort_values("amount", ascending=False).head(10)

        if margin_percentage >= 20:
            margin_health = "healthy"
        elif margin_percentage >= 5:
            margin_health = "moderate"
        elif margin_percentage >= 0:
            margin_health = "low"
        else:
            margin_health = "negative"

        return {
            "total_revenue": round(total_revenue, 2),
            "total_expenses": round(total_expenses, 2),
            "total_refunds": round(total_refunds, 2),
            "gross_margin": round(gross_margin, 2),
            "margin_percentage": round(margin_percentage, 2),
            "margin_health": margin_health,
            "top_expense_categories": expense_by_category.head(10).to_dict(orient="records"),
            "top_refund_reasons": refund_by_reason.head(10).to_dict(orient="records"),
            "unusual_expenses": unusual_expenses[
                [
                    "expense_id",
                    "merchant_id",
                    "expense_date",
                    "category",
                    "subcategory",
                    "amount",
                    "vendor_name",
                    "approval_status",
                ]
            ].to_dict(orient="records"),
            "citations": {
                "sources": [
                    "orders.csv",
                    "expenses.csv",
                    "refunds.csv",
                ]
            },
        }