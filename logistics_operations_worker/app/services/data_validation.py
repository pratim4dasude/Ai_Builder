from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"


EXPECTED_FILES = {
    "orders": "orders.csv",
    "warehouses": "warehouses.csv",
    "inventory": "inventory.csv",
    "shipments": "shipments.csv",
}


EXPECTED_COLUMNS = {
    "orders": [
        "order_id", "merchant_id", "customer_name", "customer_address",
        "area", "city", "pincode", "latitude", "longitude",
        "sku", "quantity", "order_value", "payment_type",
        "order_date", "order_status",
    ],
    "warehouses": [
        "warehouse_id", "merchant_id", "warehouse_name", "address",
        "city", "pincode", "latitude", "longitude", "zone",
        "capacity_per_day", "current_load", "cutoff_time",
    ],
    "inventory": [
        "inventory_id", "merchant_id", "warehouse_id",
        "sku", "available_qty", "reserved_qty",
    ],
    "shipments": [
        "shipment_id", "merchant_id", "order_id", "courier",
        "shipment_status", "delivery_attempts", "rto_status",
        "shipping_cost", "delivery_days", "pincode", "area", "city",
    ],
}


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(col).strip() for col in df.columns]
    return df


def read_csv_file(file_name: str) -> pd.DataFrame:
    file_path = DATA_DIR / file_name

    if not file_path.exists():
        raise FileNotFoundError(f"Missing file: {file_path}")

    df = pd.read_csv(file_path, sep=None, engine="python")
    df = clean_columns(df)
    return df


def check_required_columns(df: pd.DataFrame, expected_columns: list[str], table_name: str) -> list[str]:
    missing_columns = [col for col in expected_columns if col not in df.columns]
    if missing_columns:
        return [f"{table_name}: missing columns -> {missing_columns}. Found columns -> {df.columns.tolist()}"]
    return []


def check_missing_values(df: pd.DataFrame, table_name: str) -> list[str]:
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if not missing.empty:
        return [f"{table_name}: missing values -> {missing.to_dict()}"]
    return []


def check_duplicate_ids(df: pd.DataFrame, id_column: str, table_name: str) -> list[str]:
    if id_column not in df.columns:
        return [f"{table_name}: cannot check duplicates because {id_column} is missing"]

    duplicate_count = df[id_column].duplicated().sum()
    if duplicate_count > 0:
        return [f"{table_name}: duplicate {id_column} count -> {duplicate_count}"]
    return []


def check_bangalore_only(df: pd.DataFrame, table_name: str) -> list[str]:
    if "city" not in df.columns:
        return []

    invalid_cities = df[df["city"].astype(str).str.strip().str.lower() != "bangalore"]
    if len(invalid_cities) > 0:
        return [f"{table_name}: non-Bangalore rows found -> {len(invalid_cities)}"]
    return []


def check_lat_lon_range(df: pd.DataFrame, table_name: str) -> list[str]:
    if "latitude" not in df.columns or "longitude" not in df.columns:
        return []

    lat = pd.to_numeric(df["latitude"], errors="coerce")
    lon = pd.to_numeric(df["longitude"], errors="coerce")

    invalid_coords = df[
        lat.isna()
        | lon.isna()
        | (lat < 12.70)
        | (lat > 13.20)
        | (lon < 77.40)
        | (lon > 77.90)
    ]

    if len(invalid_coords) > 0:
        return [f"{table_name}: invalid Bangalore lat/lon rows -> {len(invalid_coords)}"]
    return []


def validate_relationships(
    orders: pd.DataFrame,
    warehouses: pd.DataFrame,
    inventory: pd.DataFrame,
    shipments: pd.DataFrame,
) -> list[str]:
    errors = []

    if "order_id" in orders.columns and "order_id" in shipments.columns:
        order_ids = set(orders["order_id"].astype(str).str.strip())
        shipment_order_ids = set(shipments["order_id"].astype(str).str.strip())

        invalid_shipment_orders = shipment_order_ids - order_ids
        if invalid_shipment_orders:
            errors.append(
                f"shipments: order_id not found in orders -> {len(invalid_shipment_orders)}"
            )

        if "order_status" in orders.columns:
            cancelled_orders = set(
                orders[
                    orders["order_status"].astype(str).str.strip().str.lower() == "cancelled"
                ]["order_id"].astype(str).str.strip()
            )

            shipments_for_cancelled = shipment_order_ids.intersection(cancelled_orders)
            if shipments_for_cancelled:
                errors.append(
                    f"shipments: shipments created for cancelled orders -> {len(shipments_for_cancelled)}"
                )

    if "warehouse_id" in warehouses.columns and "warehouse_id" in inventory.columns:
        warehouse_ids = set(warehouses["warehouse_id"].astype(str).str.strip())
        inventory_warehouse_ids = set(inventory["warehouse_id"].astype(str).str.strip())

        invalid_inventory_warehouses = inventory_warehouse_ids - warehouse_ids
        if invalid_inventory_warehouses:
            errors.append(
                f"inventory: warehouse_id not found in warehouses -> {len(invalid_inventory_warehouses)}"
            )

    if "sku" in orders.columns and "sku" in inventory.columns:
        order_skus = set(orders["sku"].astype(str).str.strip())
        inventory_skus = set(inventory["sku"].astype(str).str.strip())

        missing_skus_in_inventory = order_skus - inventory_skus
        if missing_skus_in_inventory:
            errors.append(
                f"orders: SKUs not found in inventory -> {len(missing_skus_in_inventory)}"
            )

    return errors


def safe_value_counts(df: pd.DataFrame, column: str) -> dict:
    if column not in df.columns:
        return {}

    return df[column].astype(str).str.strip().value_counts().to_dict()


def safe_nunique(df: pd.DataFrame, column: str) -> int:
    if column not in df.columns:
        return 0

    return int(df[column].astype(str).str.strip().nunique())


def safe_numeric_sum(df: pd.DataFrame, column: str) -> int:
    if column not in df.columns:
        return 0

    return int(pd.to_numeric(df[column], errors="coerce").fillna(0).sum())


def generate_data_summary(
    orders: pd.DataFrame,
    warehouses: pd.DataFrame,
    inventory: pd.DataFrame,
    shipments: pd.DataFrame,
) -> dict:
    return {
        "data_path": str(DATA_DIR),
        "row_counts": {
            "orders": len(orders),
            "warehouses": len(warehouses),
            "inventory": len(inventory),
            "shipments": len(shipments),
        },
        "orders": {
            "status_counts": safe_value_counts(orders, "order_status"),
            "payment_type_counts": safe_value_counts(orders, "payment_type"),
            "unique_skus": safe_nunique(orders, "sku"),
            "unique_areas": safe_nunique(orders, "area"),
        },
        "warehouses": {
            "unique_warehouses": safe_nunique(warehouses, "warehouse_id"),
            "total_capacity_per_day": safe_numeric_sum(warehouses, "capacity_per_day"),
        },
        "inventory": {
            "unique_skus": safe_nunique(inventory, "sku"),
            "unique_warehouses": safe_nunique(inventory, "warehouse_id"),
            "total_available_qty": safe_numeric_sum(inventory, "available_qty"),
        },
        "shipments": {
            "shipment_status_counts": safe_value_counts(shipments, "shipment_status"),
            "courier_counts": safe_value_counts(shipments, "courier"),
            "rto_counts": safe_value_counts(shipments, "rto_status"),
        },
    }


def validate_all_data() -> dict:
    errors = []

    orders = read_csv_file(EXPECTED_FILES["orders"])
    warehouses = read_csv_file(EXPECTED_FILES["warehouses"])
    inventory = read_csv_file(EXPECTED_FILES["inventory"])
    shipments = read_csv_file(EXPECTED_FILES["shipments"])

    tables = {
        "orders": orders,
        "warehouses": warehouses,
        "inventory": inventory,
        "shipments": shipments,
    }

    id_columns = {
        "orders": "order_id",
        "warehouses": "warehouse_id",
        "inventory": "inventory_id",
        "shipments": "shipment_id",
    }

    for table_name, df in tables.items():
        errors.extend(check_required_columns(df, EXPECTED_COLUMNS[table_name], table_name))
        errors.extend(check_missing_values(df, table_name))
        errors.extend(check_duplicate_ids(df, id_columns[table_name], table_name))
        errors.extend(check_bangalore_only(df, table_name))
        errors.extend(check_lat_lon_range(df, table_name))

    errors.extend(validate_relationships(orders, warehouses, inventory, shipments))

    summary = generate_data_summary(orders, warehouses, inventory, shipments)

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "summary": summary,
    }


if __name__ == "__main__":
    result = validate_all_data()

    print("DATA VALIDATION RESULT")
    print("=" * 60)
    print(f"Valid: {result['is_valid']}")

    print("\nRow counts:")
    for table, count in result["summary"]["row_counts"].items():
        print(f"- {table}: {count}")

    print("\nErrors:")
    if result["errors"]:
        for error in result["errors"]:
            print(f"- {error}")
    else:
        print("- No errors found")

    print("\nData path:")
    print(result["summary"]["data_path"])