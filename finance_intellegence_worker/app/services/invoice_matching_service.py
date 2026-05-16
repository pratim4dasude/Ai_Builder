import pandas as pd

from app.connectors.connector_manager import ConnectorManager


class InvoiceMatchingService:
    def __init__(self):
        self.connector = ConnectorManager()

    def reconcile_invoices(self) -> dict:
        invoices = self.connector.load_csv("invoices.csv")
        orders = self.connector.load_csv("orders.csv")
        payments = self.connector.load_csv("payments.csv")

        invoices["total_amount"] = pd.to_numeric(
            invoices["total_amount"],
            errors="coerce"
        ).fillna(0)

        orders["net_amount"] = pd.to_numeric(
            orders["net_amount"],
            errors="coerce"
        ).fillna(0)

        payments["amount"] = pd.to_numeric(
            payments["amount"],
            errors="coerce"
        ).fillna(0)

        valid_order_ids = set(orders["order_id"].astype(str))

        duplicate_invoice_numbers = invoices[
            invoices.duplicated("invoice_number", keep=False)
        ]

        invalid_order_invoices = invoices[
            ~invoices["order_id"].astype(str).isin(valid_order_ids)
        ]

        disputed_invoices = invoices[
            invoices["invoice_status"].astype(str).str.lower().isin(
                ["disputed", "rejected"]
            )
        ]

        high_value_invoices = invoices.sort_values(
            "total_amount",
            ascending=False
        ).head(10)

        payment_lookup = payments.groupby("order_id")["amount"].sum().to_dict()

        comparable_invoices = invoices[
            invoices["order_id"].astype(str).isin(valid_order_ids)
        ].copy()

        mismatches = []

        for _, invoice in comparable_invoices.iterrows():
            order_id = str(invoice["order_id"])
            invoice_amount = float(invoice["total_amount"])
            payment_amount = float(payment_lookup.get(order_id, 0))

            difference = round(invoice_amount - payment_amount, 2)

            # only flag meaningful mismatch, not every small difference
            if abs(difference) > max(500, payment_amount * 0.15):
                mismatches.append({
                    "invoice_id": invoice.get("invoice_id"),
                    "invoice_number": invoice.get("invoice_number"),
                    "order_id": order_id,
                    "invoice_amount": round(invoice_amount, 2),
                    "payment_amount": round(payment_amount, 2),
                    "difference": difference,
                    "invoice_status": invoice.get("invoice_status"),
                })

        return {
            "total_invoices": int(len(invoices)),
            "duplicate_invoice_count": int(len(duplicate_invoice_numbers)),
            "invalid_order_invoice_count": int(len(invalid_order_invoices)),
            "disputed_invoice_count": int(len(disputed_invoices)),
            "payment_mismatch_count": int(len(mismatches)),
            "top_payment_mismatches": mismatches[:10],
            "top_high_value_invoices": high_value_invoices[
                [
                    "invoice_id",
                    "invoice_number",
                    "vendor_name",
                    "order_id",
                    "total_amount",
                    "invoice_status",
                ]
            ].to_dict(orient="records"),
            "citations": {
                "sources": [
                    "invoices.csv",
                    "orders.csv",
                    "payments.csv",
                ]
            },
        }