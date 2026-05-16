from app.connectors.connector_manager import ConnectorManager


class FinanceDataValidationService:
    def __init__(self):
        self.connector = ConnectorManager()

    def validate_required_files(self) -> dict:
        required_files = [
            "orders.csv",
            "payments.csv",
            "invoices.csv",
            "refunds.csv",
            "expenses.csv",
        ]

        missing = []

        for file in required_files:
            try:
                self.connector.load_csv(file)
            except FileNotFoundError:
                missing.append(file)

        return {
            "is_valid": len(missing) == 0,
            "missing_files": missing,
            "required_files": required_files,
        }

    def validate_columns(self) -> dict:
        expected_columns = {
            "orders.csv": [
                "merchant_id",
                "order_id",
                "customer_id",
                "order_date",
                "sku",
                "category",
                "quantity",
                "gross_amount",
                "discount_amount",
                "tax_amount",
                "net_amount",
                "payment_method",
                "order_status",
                "city",
                "state",
                "shipment_days",
                "delivery_status",
            ],
            "payments.csv": [
                "merchant_id",
                "payment_id",
                "order_id",
                "payment_date",
                "payment_method",
                "payment_status",
                "amount",
                "refund_amount",
                "settlement_date",
                "gateway_name",
            ],
            "invoices.csv": [
                "merchant_id",
                "invoice_id",
                "order_id",
                "vendor_name",
                "invoice_number",
                "invoice_date",
                "billing_period_start",
                "billing_period_end",
                "subtotal",
                "tax_amount",
                "total_amount",
                "currency",
                "invoice_status",
            ],
            "refunds.csv": [
                "merchant_id",
                "refund_id",
                "order_id",
                "refund_amount",
                "refund_reason",
                "deduction_reason",
                "dispute_status",
                "created_at",
                "resolved_at",
                "customer_complaint_score",
            ],
            "expenses.csv": [
                "expense_id",
                "merchant_id",
                "expense_date",
                "category",
                "subcategory",
                "amount",
                "payment_mode",
                "vendor_name",
                "approval_status",
            ],
        }

        checks = {}

        for file, columns in expected_columns.items():
            try:
                df = self.connector.load_csv(file)

                missing_cols = [
                    col for col in columns
                    if col not in df.columns
                ]

                checks[file] = {
                    "is_valid": len(missing_cols) == 0,
                    "missing_columns": missing_cols,
                    "row_count": len(df),
                    "columns_found": list(df.columns),
                }

            except FileNotFoundError:
                checks[file] = {
                    "is_valid": False,
                    "missing_columns": columns,
                    "row_count": 0,
                    "columns_found": [],
                    "error": "file_not_found",
                }

        return checks