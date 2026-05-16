import pandas as pd

from app.connectors.connector_manager import ConnectorManager
from app.utils.period_parser import filter_by_date
from app.ml.revenue_xgboost import RevenueXGBoostModel


class RevenueForecastService:
    def __init__(self):
        self.connector = ConnectorManager()

    def analyze_revenue(self, period=None) -> dict:
        orders_all = self.connector.load_csv("orders.csv")

        start_date = period.get("start_date") if period else None
        end_date = period.get("end_date") if period else None

        orders = filter_by_date(
            orders_all,
            "order_date",
            start_date,
            end_date,
        )

        orders["order_date"] = pd.to_datetime(
            orders["order_date"],
            errors="coerce",
        )

        orders["net_amount"] = pd.to_numeric(
            orders["net_amount"],
            errors="coerce",
        ).fillna(0)

        total_revenue = float(orders["net_amount"].sum())
        total_orders = int(len(orders))
        avg_order_value = float(orders["net_amount"].mean()) if total_orders else 0

        daily_revenue = (
            orders.groupby(orders["order_date"].dt.date)["net_amount"]
            .sum()
            .reset_index()
            .rename(columns={"order_date": "date", "net_amount": "revenue"})
        )

        top_days = daily_revenue.sort_values(
            "revenue",
            ascending=False,
        ).head(5)

        category_revenue = (
            orders.groupby("category")["net_amount"]
            .sum()
            .reset_index()
            .sort_values("net_amount", ascending=False)
            if len(orders) else pd.DataFrame(columns=["category", "net_amount"])
        )

        xgb_forecast = RevenueXGBoostModel().train_and_forecast(
            orders=orders_all,
            horizon_days=7,
        )

        return {
            "period": period,
            "row_count": total_orders,
            "total_revenue": round(total_revenue, 2),
            "total_orders": total_orders,
            "avg_order_value": round(avg_order_value, 2),
            "forecast_next_7_days": xgb_forecast["forecast_next_7_days"],
            "forecast_method": xgb_forecast["model_used"],
            "xgboost_forecast": xgb_forecast,
            "top_revenue_days": top_days.to_dict(orient="records"),
            "category_revenue": category_revenue.to_dict(orient="records"),
            "citations": {
                "source": "orders.csv",
            },
        }