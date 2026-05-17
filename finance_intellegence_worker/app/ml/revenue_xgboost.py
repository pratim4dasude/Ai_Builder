import json
import pickle
from pathlib import Path

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

        self.feature_cols = [
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

        self.artifact_dir = Path("artifacts/models")
        self.model_path = self.artifact_dir / "revenue_xgboost.pkl"
        self.metadata_path = self.artifact_dir / "revenue_xgboost_metadata.json"

        self.metadata = {}

        self.artifact_dir.mkdir(parents=True, exist_ok=True)

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

        orders = orders.dropna(subset=["order_date"])

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

    def model_exists(self) -> bool:
        return self.model_path.exists() and self.metadata_path.exists()

    def save_model(self):
        self.artifact_dir.mkdir(parents=True, exist_ok=True)

        with open(self.model_path, "wb") as f:
            pickle.dump(self.model, f)

        with open(self.metadata_path, "w") as f:
            json.dump(self.metadata, f, indent=2)

    def load_model(self) -> bool:
        if not self.model_exists():
            return False

        try:
            with open(self.model_path, "rb") as f:
                self.model = pickle.load(f)

            with open(self.metadata_path, "r") as f:
                self.metadata = json.load(f)

            return True

        except Exception:
            return False

    def should_retrain(self, daily: pd.DataFrame) -> bool:
        if not self.model_exists():
            return True

        loaded = self.load_model()

        if not loaded:
            return True

        last_training_date = self.metadata.get("last_training_date")

        if not last_training_date:
            return True

        latest_data_date = str(daily["date"].max().date())

        return latest_data_date > last_training_date
    def train(self, orders: pd.DataFrame) -> dict:
        daily = self._prepare_daily_data(orders)

        if len(daily) < 20:
            return {
                "model_used": "moving_average_fallback",
                "model_saved": False,
                "reason": "Not enough daily data for XGBoost training.",
                "model_metrics": {},
                "features_used": self.feature_cols,
            }

        X = daily[self.feature_cols]
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

        self.metadata = {
            "model_used": "xgboost_regressor",
            "features_used": self.feature_cols,
            "model_metrics": {
                "mae": round(float(mae), 2),
                "mape": round(float(mape), 2),
                "train_days": int(len(X_train)),
                "test_days": int(len(X_test)),
            },
            "training_rows": int(len(daily)),
            "last_training_date": str(daily["date"].max().date()),
        }

        self.save_model()

        return {
            "model_used": "xgboost_regressor",
            "model_saved": True,
            "model_path": str(self.model_path),
            "metadata_path": str(self.metadata_path),
            "model_metrics": self.metadata["model_metrics"],
            "features_used": self.feature_cols,
        }

    def predict_next_days(self, orders: pd.DataFrame, horizon_days: int = 7) -> dict:
        daily = self._prepare_daily_data(orders)

        if len(daily) < 20:
            return self._moving_average_fallback(daily, horizon_days)

        retrained_now = False
        model_loaded = False
        retrain_reason = None

        if self.should_retrain(daily):
            previous_training_date = self.metadata.get("last_training_date")

            train_result = self.train(orders)
            retrained_now = True

            if train_result["model_used"] != "xgboost_regressor":
                return self._moving_average_fallback(daily, horizon_days)

            model_loaded = self.load_model()

            retrain_reason = {
                "reason": "model_missing_or_new_data_detected",
                "previous_training_date": previous_training_date,
                "latest_data_date": str(daily["date"].max().date()),
            }

        else:
            model_loaded = self.load_model()

        if not model_loaded:
            return self._moving_average_fallback(daily, horizon_days)

        future_rows = []
        history = daily.copy()

        for _ in range(horizon_days):
            next_date = history["date"].max() + pd.Timedelta(days=1)

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

            X_future = pd.DataFrame([next_row])[self.feature_cols]

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

        forecast_total = sum(row["predicted_revenue"] for row in future_rows)

        return {
            "model_used": "xgboost_regressor",
            "model_loaded_from_disk": model_loaded,
            "trained_now": retrained_now,
            "retrain_reason": retrain_reason,
            "model_path": str(self.model_path),
            "metadata_path": str(self.metadata_path),
            "forecast_next_7_days": round(float(forecast_total), 2),
            "daily_forecast": future_rows,
            "model_metrics": self.metadata.get("model_metrics", {}),
            "features_used": self.metadata.get("features_used", self.feature_cols),
            "last_training_date": self.metadata.get("last_training_date"),
        }

    def train_and_forecast(self, orders: pd.DataFrame, horizon_days: int = 7) -> dict:
        return self.predict_next_days(
            orders=orders,
            horizon_days=horizon_days,
        )

    def _moving_average_fallback(self, daily: pd.DataFrame, horizon_days: int) -> dict:
        if len(daily) == 0:
            return {
                "model_used": "moving_average_fallback",
                "reason": "No revenue data available.",
                "forecast_next_7_days": 0,
                "daily_forecast": [],
                "model_metrics": {},
                "features_used": [],
            }

        avg_revenue = float(daily["revenue"].tail(7).mean())
        last_date = daily["date"].max()

        daily_forecast = []

        for i in range(horizon_days):
            next_date = last_date + pd.Timedelta(days=i + 1)

            daily_forecast.append({
                "date": str(next_date.date()),
                "predicted_revenue": round(avg_revenue, 2),
            })

        return {
            "model_used": "moving_average_fallback",
            "reason": "Not enough data or model unavailable.",
            "forecast_next_7_days": round(avg_revenue * horizon_days, 2),
            "daily_forecast": daily_forecast,
            "model_metrics": {},
            "features_used": [],
        }