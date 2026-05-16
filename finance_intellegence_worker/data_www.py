from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path(__file__).resolve().parent / "data"

FILES = [
    "orders.csv",
    "payments.csv",
    "invoices.csv",
    "refunds.csv",
    "expenses.csv",
]


def check_file(file_name: str):
    file_path = DATA_DIR / file_name

    if not file_path.exists():
        print(f"\n{file_name}")
        print("Status: Missing file")
        return

    df = pd.read_csv(file_path)

    rows = len(df)
    columns = len(df.columns)

    nan_count = int(df.isna().sum().sum())
    blank_count = int(
        df.astype(str).apply(lambda col: col.str.strip().eq("")).sum().sum()
    )

    numeric_df = df.select_dtypes(include=[np.number])
    infinity_count = int(np.isinf(numeric_df).sum().sum()) if not numeric_df.empty else 0

    print(f"\n{file_name}")
    print("-" * 40)
    print(f"Rows: {rows}")
    print(f"Columns: {columns}")
    print(f"NaN values: {nan_count}")
    print(f"Blank string values: {blank_count}")
    print(f"Infinity values: {infinity_count}")

    missing_by_column = df.isna().sum()
    missing_by_column = missing_by_column[missing_by_column > 0]

    if not missing_by_column.empty:
        print("Columns with missing values:")
        for col, count in missing_by_column.items():
            print(f"  {col}: {int(count)}")
    else:
        print("Columns with missing values: None")


def main():
    print(f"Checking data folder: {DATA_DIR}")

    for file_name in FILES:
        check_file(file_name)


if __name__ == "__main__":
    main()