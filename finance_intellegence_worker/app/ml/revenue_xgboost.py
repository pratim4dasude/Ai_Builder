import pandas as pd
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error


class RevenueXGBoostModel:
    def __init__(self):
        self.model = XGBRegressor(
            n_estimators=120,
            max_depth=4,
            learning_rate=0.08,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=42,
        )

    def _prepare_daily_data(self, orders: pd.DataFrame) -> pd.DataFrame:
        orders = orders.copy()

        orders["order_date"] = pd.to_datetime(
            orders["order_date"],
            errors="coerce",
        )

        orders["net_amount"] = pd.to_numeric(
            orders["net_amount"],
            errors="coerce",
        ).fillna(0)

        daily = (
            orders.groupby(orders["order_date"].dt.date)
            .agg(
                revenue=("net_amount", "sum"),
                order_count=("order_id", "count"),
                avg_order_value=("net_amount", "mean"),
            )
            .reset_index()
        )

        daily["date"] = pd.to_datetime(daily["order_date"])
        daily = daily.drop(columns=["order_date"])
        daily = daily.sort_values("date")

        daily["day_of_week"] = daily["date"].dt.dayofweek
        daily["day"] = daily["date"].dt.day
        daily["month"] = daily["date"].dt.month
        daily["week_of_year"] = daily["date"].dt.isocalendar().week.astype(int)

        daily["lag_1_revenue"] = daily["revenue"].shift(1)
        daily["lag_3_revenue"] = daily["revenue"].shift(3)
        daily["lag_7_revenue"] = daily["revenue"].shift(7)

        daily["rolling_3_revenue"] = daily["revenue"].shift(1).rolling(3).mean()
        daily["rolling_7_revenue"] = daily["revenue"].shift(1).rolling(7).mean()

        daily = daily.dropna().reset_index(drop=True)

        return daily

    def train_and_forecast(self, orders: pd.DataFrame, horizon_days: int = 7) -> dict:
        daily = self._prepare_daily_data(orders)

        if len(daily) < 20:
            return {
                "model_used": "moving_average_fallback",
                "reason": "Not enough daily data for XGBoost training.",
                "forecast_next_7_days": round(float(daily["revenue"].tail(7).mean() * 7), 2)
                if len(daily) else 0,
                "daily_forecast": [],
                "model_metrics": {},
            }

        feature_cols = [
            "order_count",
            "avg_order_value",
            "day_of_week",
            "day",
            "month",
            "week_of_year",
            "lag_1_revenue",
            "lag_3_revenue",
            "lag_7_revenue",
            "rolling_3_revenue",
            "rolling_7_revenue",
        ]

        X = daily[feature_cols]
        y = daily["revenue"]

        split_index = int(len(daily) * 0.8)

        X_train = X.iloc[:split_index]
        y_train = y.iloc[:split_index]

        X_test = X.iloc[split_index:]
        y_test = y.iloc[split_index:]

        self.model.fit(X_train, y_train)

        test_pred = self.model.predict(X_test)

        mae = mean_absolute_error(y_test, test_pred)
        mape = mean_absolute_percentage_error(y_test, test_pred) * 100

        future_rows = []
        history = daily.copy()

        for i in range(horizon_days):
            next_date = history["date"].max() + pd.Timedelta(days=1)

            last_rows = history.tail(7)

            next_row = {
                "date": next_date,
                "order_count": float(history["order_count"].tail(7).mean()),
                "avg_order_value": float(history["avg_order_value"].tail(7).mean()),
                "day_of_week": next_date.dayofweek,
                "day": next_date.day,
                "month": next_date.month,
                "week_of_year": int(next_date.isocalendar().week),
                "lag_1_revenue": float(history["revenue"].iloc[-1]),
                "lag_3_revenue": float(history["revenue"].iloc[-3]),
                "lag_7_revenue": float(history["revenue"].iloc[-7]),
                "rolling_3_revenue": float(history["revenue"].tail(3).mean()),
                "rolling_7_revenue": float(history["revenue"].tail(7).mean()),
            }

            X_future = pd.DataFrame([next_row])[feature_cols]
            predicted_revenue = float(self.model.predict(X_future)[0])

            predicted_revenue = max(predicted_revenue, 0)

            future_rows.append({
                "date": str(next_date.date()),
                "predicted_revenue": round(predicted_revenue, 2),
            })

            history = pd.concat(
                [
                    history,
                    pd.DataFrame([
                        {
                            **next_row,
                            "revenue": predicted_revenue,
                        }
                    ]),
                ],
                ignore_index=True,
            )

        forecast_next_7_days = sum(
            row["predicted_revenue"]
            for row in future_rows
        )

        return {
            "model_used": "xgboost_regressor",
            "forecast_next_7_days": round(float(forecast_next_7_days), 2),
            "daily_forecast": future_rows,
            "model_metrics": {
                "mae": round(float(mae), 2),
                "mape": round(float(mape), 2),
                "train_days": int(len(X_train)),
                "test_days": int(len(X_test)),
            },
            "features_used": feature_cols,
        }