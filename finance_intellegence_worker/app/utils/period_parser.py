from datetime import datetime, timedelta
from typing import Optional, Tuple

import pandas as pd


def get_dataset_date_range(orders_df) -> Tuple[Optional[pd.Timestamp], Optional[pd.Timestamp]]:
    orders_df = orders_df.copy()
    orders_df["order_date"] = pd.to_datetime(orders_df["order_date"], errors="coerce")
    valid_dates = orders_df["order_date"].dropna()

    if valid_dates.empty:
        return None, None

    return valid_dates.min(), valid_dates.max()


def parse_period_from_query(query: str, orders_df=None) -> dict:
    query = query.lower()

    dataset_min_date = None
    dataset_max_date = None

    if orders_df is not None:
        dataset_min_date, dataset_max_date = get_dataset_date_range(orders_df)

    reference_date = dataset_max_date if dataset_max_date is not None else pd.Timestamp(datetime.now())

    start_date = None
    end_date = None
    period_label = "all_data"

    if "today" in query:
        start_date = reference_date.normalize()
        end_date = reference_date.normalize()
        period_label = "today"

    elif "yesterday" in query:
        date = reference_date.normalize() - timedelta(days=1)
        start_date = date
        end_date = date
        period_label = "yesterday"

    elif "last 7 days" in query or "past 7 days" in query:
        end_date = reference_date.normalize()
        start_date = end_date - timedelta(days=6)
        period_label = "last_7_days"

    elif "last 30 days" in query or "past 30 days" in query:
        end_date = reference_date.normalize()
        start_date = end_date - timedelta(days=29)
        period_label = "last_30_days"

    elif "this month" in query or "current month" in query:
        end_date = reference_date.normalize()
        start_date = pd.Timestamp(year=end_date.year, month=end_date.month, day=1)
        period_label = "this_month"

    elif "last month" in query or "previous month" in query:
        first_day_current_month = pd.Timestamp(
            year=reference_date.year,
            month=reference_date.month,
            day=1,
        )
        end_date = first_day_current_month - timedelta(days=1)
        start_date = pd.Timestamp(
            year=end_date.year,
            month=end_date.month,
            day=1,
        )
        period_label = "last_month"

    else:
        start_date = dataset_min_date
        end_date = dataset_max_date
        period_label = "all_data"

    return {
        "period_label": period_label,
        "start_date": str(start_date.date()) if start_date is not None else None,
        "end_date": str(end_date.date()) if end_date is not None else None,
        "dataset_min_date": str(dataset_min_date.date()) if dataset_min_date is not None else None,
        "dataset_max_date": str(dataset_max_date.date()) if dataset_max_date is not None else None,
    }


def filter_by_date(df, date_column: str, start_date: Optional[str], end_date: Optional[str]):
    if df is None or df.empty:
        return df

    if date_column not in df.columns:
        return df

    if not start_date or not end_date:
        return df

    df = df.copy()
    df[date_column] = pd.to_datetime(df[date_column], errors="coerce")

    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)

    return df[
        (df[date_column] >= start) &
        (df[date_column] <= end)
    ]