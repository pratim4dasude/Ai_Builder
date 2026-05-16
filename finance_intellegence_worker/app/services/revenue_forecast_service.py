import pandas as pd
from app.connectors.connector_manager import ConnectorManager


class RevenueForecastService:
    def __init__(self):
        self.connector = ConnectorManager()

    def analyze_revenue(self) -> dict:
        orders = self.connector.load_csv("orders.csv")

        orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")
        orders["net_amount"] = pd.to_numeric(orders["net_amount"], errors="coerce").fillna(0)

        total_revenue = float(orders["net_amount"].sum())
        total_orders = int(len(orders))
        avg_order_value = float(orders["net_amount"].mean()) if total_orders else 0

        daily_revenue = (
            orders.groupby(orders["order_date"].dt.date)["net_amount"]
            .sum()
            .reset_index()
            .rename(columns={"order_date": "date", "net_amount": "revenue"})
        )

        last_7_day_avg = float(daily_revenue["revenue"].tail(7).mean()) if len(daily_revenue) else 0
        forecast_next_7_days = last_7_day_avg * 7

        top_days = daily_revenue.sort_values("revenue", ascending=False).head(5)

        return {
            "total_revenue": round(total_revenue, 2),
            "total_orders": total_orders,
            "avg_order_value": round(avg_order_value, 2),
            "forecast_next_7_days": round(float(forecast_next_7_days), 2),
            "top_revenue_days": top_days.to_dict(orient="records"),
            "citations": {
                "source": "orders.csv",
                "rows_used": list(range(1, min(len(orders), 50) + 1)),
            },
        }