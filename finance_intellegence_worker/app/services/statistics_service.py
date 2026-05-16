# import pandas as pd
#
# from app.connectors.connector_manager import ConnectorManager
#
#
# class StatisticsService:
#     def __init__(self):
#         self.connector = ConnectorManager()
#
#     def analyze_statistics(self) -> dict:
#         orders = self.connector.load_csv("orders.csv")
#         payments = self.connector.load_csv("payments.csv")
#         invoices = self.connector.load_csv("invoices.csv")
#         refunds = self.connector.load_csv("refunds.csv")
#         expenses = self.connector.load_csv("expenses.csv")
#
#         orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")
#         orders["net_amount"] = pd.to_numeric(orders["net_amount"], errors="coerce").fillna(0)
#         orders["quantity"] = pd.to_numeric(orders["quantity"], errors="coerce").fillna(0)
#
#         payments["amount"] = pd.to_numeric(payments["amount"], errors="coerce").fillna(0)
#         payments["refund_amount"] = pd.to_numeric(payments["refund_amount"], errors="coerce").fillna(0)
#
#         invoices["total_amount"] = pd.to_numeric(invoices["total_amount"], errors="coerce").fillna(0)
#
#         refunds["refund_amount"] = pd.to_numeric(refunds["refund_amount"], errors="coerce").fillna(0)
#         refunds["customer_complaint_score"] = pd.to_numeric(
#             refunds["customer_complaint_score"],
#             errors="coerce",
#         ).fillna(0)
#
#         expenses["amount"] = pd.to_numeric(expenses["amount"], errors="coerce").fillna(0)
#
#         total_revenue = float(orders["net_amount"].sum())
#         total_orders = int(len(orders))
#         total_payments = float(payments["amount"].sum())
#         total_refunds = float(refunds["refund_amount"].sum())
#         total_expenses = float(expenses["amount"].sum())
#         gross_margin = total_revenue - total_expenses - total_refunds
#
#         avg_order_value = float(orders["net_amount"].mean())
#         median_order_value = float(orders["net_amount"].median())
#         std_order_value = float(orders["net_amount"].std())
#         p75_order_value = float(orders["net_amount"].quantile(0.75))
#         p90_order_value = float(orders["net_amount"].quantile(0.90))
#         p95_order_value = float(orders["net_amount"].quantile(0.95))
#
#         refund_rate = (total_refunds / total_payments) * 100 if total_payments else 0
#         expense_to_revenue_ratio = (total_expenses / total_revenue) * 100 if total_revenue else 0
#         gross_margin_percentage = (gross_margin / total_revenue) * 100 if total_revenue else 0
#
#         failed_payment_count = int(
#             payments["payment_status"].astype(str).str.lower().eq("failed").sum()
#         )
#         failed_payment_rate = (
#             failed_payment_count / len(payments) * 100
#             if len(payments) else 0
#         )
#
#         duplicate_invoice_count = int(
#             invoices.duplicated("invoice_number", keep=False).sum()
#         )
#
#         valid_order_ids = set(orders["order_id"].astype(str))
#         invalid_invoice_count = int(
#             (~invoices["order_id"].astype(str).isin(valid_order_ids)).sum()
#         )
#
#         disputed_invoice_count = int(
#             invoices["invoice_status"]
#             .astype(str)
#             .str.lower()
#             .isin(["disputed", "rejected"])
#             .sum()
#         )
#
#         category_revenue = (
#             orders.groupby("category")["net_amount"]
#             .agg(["sum", "mean", "count"])
#             .reset_index()
#             .sort_values("sum", ascending=False)
#         )
#
#         payment_mix = (
#             payments["payment_status"]
#             .value_counts()
#             .reset_index()
#         )
#         payment_mix.columns = ["payment_status", "count"]
#
#         refund_reason_stats = (
#             refunds.groupby("refund_reason")["refund_amount"]
#             .agg(["sum", "mean", "count"])
#             .reset_index()
#             .sort_values("sum", ascending=False)
#         )
#
#         expense_category_stats = (
#             expenses.groupby("category")["amount"]
#             .agg(["sum", "mean", "count"])
#             .reset_index()
#             .sort_values("sum", ascending=False)
#         )
#
#         invoice_status_mix = (
#             invoices["invoice_status"]
#             .value_counts()
#             .reset_index()
#         )
#         invoice_status_mix.columns = ["invoice_status", "count"]
#
#         risk_flags = []
#
#         if refund_rate > 8:
#             risk_flags.append({
#                 "risk": "high_refund_leakage",
#                 "severity": "high",
#                 "reason": f"Refund leakage is {refund_rate:.2f}%, above the 8% threshold.",
#             })
#         elif refund_rate > 5:
#             risk_flags.append({
#                 "risk": "moderate_refund_leakage",
#                 "severity": "medium",
#                 "reason": f"Refund leakage is {refund_rate:.2f}%, above the 5% watch level.",
#             })
#
#         if expense_to_revenue_ratio > 80:
#             risk_flags.append({
#                 "risk": "high_expense_ratio",
#                 "severity": "high",
#                 "reason": f"Expenses are {expense_to_revenue_ratio:.2f}% of revenue.",
#             })
#         elif expense_to_revenue_ratio > 65:
#             risk_flags.append({
#                 "risk": "moderate_expense_ratio",
#                 "severity": "medium",
#                 "reason": f"Expenses are {expense_to_revenue_ratio:.2f}% of revenue.",
#             })
#
#         if gross_margin_percentage < 10:
#             risk_flags.append({
#                 "risk": "low_margin",
#                 "severity": "high",
#                 "reason": f"Gross margin is only {gross_margin_percentage:.2f}%.",
#             })
#
#         if failed_payment_rate > 8:
#             risk_flags.append({
#                 "risk": "high_failed_payment_rate",
#                 "severity": "medium",
#                 "reason": f"Failed payment rate is {failed_payment_rate:.2f}%.",
#             })
#
#         duplicate_invoice_rate = (
#             duplicate_invoice_count / len(invoices) * 100
#             if len(invoices) else 0
#         )
#
#         invalid_invoice_rate = (
#             invalid_invoice_count / len(invoices) * 100
#             if len(invoices) else 0
#         )
#
#         disputed_invoice_rate = (
#             disputed_invoice_count / len(invoices) * 100
#             if len(invoices) else 0
#         )
#
#         if duplicate_invoice_rate > 3:
#             risk_flags.append({
#                 "risk": "duplicate_invoice_risk",
#                 "severity": "medium",
#                 "reason": f"Duplicate invoice rate is {duplicate_invoice_rate:.2f}%.",
#             })
#
#         if invalid_invoice_rate > 5:
#             risk_flags.append({
#                 "risk": "invalid_invoice_mapping",
#                 "severity": "high",
#                 "reason": f"Invalid invoice-order mapping rate is {invalid_invoice_rate:.2f}%.",
#             })
#
#         if disputed_invoice_rate > 8:
#             risk_flags.append({
#                 "risk": "high_disputed_invoice_rate",
#                 "severity": "medium",
#                 "reason": f"Disputed/rejected invoice rate is {disputed_invoice_rate:.2f}%.",
#             })
#
#         return {
#             "core_metrics": {
#                 "total_revenue": round(total_revenue, 2),
#                 "total_orders": total_orders,
#                 "total_payments": round(total_payments, 2),
#                 "total_refunds": round(total_refunds, 2),
#                 "total_expenses": round(total_expenses, 2),
#                 "gross_margin": round(gross_margin, 2),
#                 "gross_margin_percentage": round(gross_margin_percentage, 2),
#                 "refund_leakage_rate": round(refund_rate, 2),
#                 "expense_to_revenue_ratio": round(expense_to_revenue_ratio, 2),
#                 "failed_payment_rate": round(failed_payment_rate, 2),
#             },
#             "order_value_distribution": {
#                 "average_order_value": round(avg_order_value, 2),
#                 "median_order_value": round(median_order_value, 2),
#                 "standard_deviation": round(std_order_value, 2),
#                 "p75_order_value": round(p75_order_value, 2),
#                 "p90_order_value": round(p90_order_value, 2),
#                 "p95_order_value": round(p95_order_value, 2),
#             },
#             "invoice_quality_metrics": {
#                 "total_invoices": int(len(invoices)),
#                 "duplicate_invoice_count": duplicate_invoice_count,
#                 "duplicate_invoice_rate": round(duplicate_invoice_rate, 2),
#                 "invalid_invoice_count": invalid_invoice_count,
#                 "invalid_invoice_rate": round(invalid_invoice_rate, 2),
#                 "disputed_invoice_count": disputed_invoice_count,
#                 "disputed_invoice_rate": round(disputed_invoice_rate, 2),
#             },
#             "category_revenue": category_revenue.head(10).to_dict(orient="records"),
#             "payment_status_mix": payment_mix.to_dict(orient="records"),
#             "refund_reason_stats": refund_reason_stats.head(10).to_dict(orient="records"),
#             "expense_category_stats": expense_category_stats.head(10).to_dict(orient="records"),
#             "invoice_status_mix": invoice_status_mix.to_dict(orient="records"),
#             "risk_flags": risk_flags,
#             "citations": {
#                 "sources": [
#                     "orders.csv",
#                     "payments.csv",
#                     "invoices.csv",
#                     "refunds.csv",
#                     "expenses.csv",
#                 ]
#             },
#         }


import pandas as pd

from app.connectors.connector_manager import ConnectorManager
from app.utils.period_parser import filter_by_date


class StatisticsService:
    def __init__(self):
        self.connector = ConnectorManager()

    def analyze_statistics(self, period=None) -> dict:
        orders = self.connector.load_csv("orders.csv")
        payments = self.connector.load_csv("payments.csv")
        invoices = self.connector.load_csv("invoices.csv")
        refunds = self.connector.load_csv("refunds.csv")
        expenses = self.connector.load_csv("expenses.csv")

        start_date = period.get("start_date") if period else None
        end_date = period.get("end_date") if period else None

        orders = filter_by_date(orders, "order_date", start_date, end_date)
        payments = filter_by_date(payments, "payment_date", start_date, end_date)
        invoices = filter_by_date(invoices, "invoice_date", start_date, end_date)
        refunds = filter_by_date(refunds, "created_at", start_date, end_date)
        expenses = filter_by_date(expenses, "expense_date", start_date, end_date)

        orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")
        orders["net_amount"] = pd.to_numeric(orders["net_amount"], errors="coerce").fillna(0)
        orders["quantity"] = pd.to_numeric(orders["quantity"], errors="coerce").fillna(0)

        payments["amount"] = pd.to_numeric(payments["amount"], errors="coerce").fillna(0)
        payments["refund_amount"] = pd.to_numeric(payments["refund_amount"], errors="coerce").fillna(0)

        invoices["total_amount"] = pd.to_numeric(invoices["total_amount"], errors="coerce").fillna(0)

        refunds["refund_amount"] = pd.to_numeric(refunds["refund_amount"], errors="coerce").fillna(0)
        refunds["customer_complaint_score"] = pd.to_numeric(
            refunds["customer_complaint_score"],
            errors="coerce",
        ).fillna(0)

        expenses["amount"] = pd.to_numeric(expenses["amount"], errors="coerce").fillna(0)

        total_revenue = float(orders["net_amount"].sum())
        total_orders = int(len(orders))
        total_payments = float(payments["amount"].sum())
        total_refunds = float(refunds["refund_amount"].sum())
        total_expenses = float(expenses["amount"].sum())
        gross_margin = total_revenue - total_expenses - total_refunds

        avg_order_value = float(orders["net_amount"].mean()) if len(orders) else 0
        median_order_value = float(orders["net_amount"].median()) if len(orders) else 0
        std_order_value = float(orders["net_amount"].std()) if len(orders) else 0
        p75_order_value = float(orders["net_amount"].quantile(0.75)) if len(orders) else 0
        p90_order_value = float(orders["net_amount"].quantile(0.90)) if len(orders) else 0
        p95_order_value = float(orders["net_amount"].quantile(0.95)) if len(orders) else 0

        refund_rate = (total_refunds / total_payments) * 100 if total_payments else 0
        expense_to_revenue_ratio = (total_expenses / total_revenue) * 100 if total_revenue else 0
        gross_margin_percentage = (gross_margin / total_revenue) * 100 if total_revenue else 0

        failed_payment_count = int(
            payments["payment_status"].astype(str).str.lower().eq("failed").sum()
        ) if len(payments) else 0

        failed_payment_rate = (
            failed_payment_count / len(payments) * 100
            if len(payments) else 0
        )

        duplicate_invoice_count = int(
            invoices.duplicated("invoice_number", keep=False).sum()
        ) if len(invoices) else 0

        valid_order_ids = set(orders["order_id"].astype(str))

        invalid_invoice_count = int(
            (~invoices["order_id"].astype(str).isin(valid_order_ids)).sum()
        ) if len(invoices) else 0

        disputed_invoice_count = int(
            invoices["invoice_status"]
            .astype(str)
            .str.lower()
            .isin(["disputed", "rejected"])
            .sum()
        ) if len(invoices) else 0

        duplicate_invoice_rate = (
            duplicate_invoice_count / len(invoices) * 100
            if len(invoices) else 0
        )

        invalid_invoice_rate = (
            invalid_invoice_count / len(invoices) * 100
            if len(invoices) else 0
        )

        disputed_invoice_rate = (
            disputed_invoice_count / len(invoices) * 100
            if len(invoices) else 0
        )

        if len(orders):
            category_revenue = (
                orders.groupby("category")["net_amount"]
                .agg(["sum", "mean", "count"])
                .reset_index()
                .sort_values("sum", ascending=False)
            )
        else:
            category_revenue = pd.DataFrame(columns=["category", "sum", "mean", "count"])

        if len(payments):
            payment_mix = payments["payment_status"].value_counts().reset_index()
            payment_mix.columns = ["payment_status", "count"]
        else:
            payment_mix = pd.DataFrame(columns=["payment_status", "count"])

        if len(refunds):
            refund_reason_stats = (
                refunds.groupby("refund_reason")["refund_amount"]
                .agg(["sum", "mean", "count"])
                .reset_index()
                .sort_values("sum", ascending=False)
            )
        else:
            refund_reason_stats = pd.DataFrame(columns=["refund_reason", "sum", "mean", "count"])

        if len(expenses):
            expense_category_stats = (
                expenses.groupby("category")["amount"]
                .agg(["sum", "mean", "count"])
                .reset_index()
                .sort_values("sum", ascending=False)
            )
        else:
            expense_category_stats = pd.DataFrame(columns=["category", "sum", "mean", "count"])

        if len(invoices):
            invoice_status_mix = invoices["invoice_status"].value_counts().reset_index()
            invoice_status_mix.columns = ["invoice_status", "count"]
        else:
            invoice_status_mix = pd.DataFrame(columns=["invoice_status", "count"])

        risk_flags = []

        if refund_rate > 8:
            risk_flags.append({
                "risk": "high_refund_leakage",
                "severity": "high",
                "reason": f"Refund leakage is {refund_rate:.2f}%, above the 8% threshold.",
            })
        elif refund_rate > 5:
            risk_flags.append({
                "risk": "moderate_refund_leakage",
                "severity": "medium",
                "reason": f"Refund leakage is {refund_rate:.2f}%, above the 5% watch level.",
            })

        if expense_to_revenue_ratio > 80:
            risk_flags.append({
                "risk": "high_expense_ratio",
                "severity": "high",
                "reason": f"Expenses are {expense_to_revenue_ratio:.2f}% of revenue.",
            })
        elif expense_to_revenue_ratio > 65:
            risk_flags.append({
                "risk": "moderate_expense_ratio",
                "severity": "medium",
                "reason": f"Expenses are {expense_to_revenue_ratio:.2f}% of revenue.",
            })

        if gross_margin_percentage < 10:
            risk_flags.append({
                "risk": "low_margin",
                "severity": "high",
                "reason": f"Gross margin is only {gross_margin_percentage:.2f}%.",
            })

        if failed_payment_rate > 8:
            risk_flags.append({
                "risk": "high_failed_payment_rate",
                "severity": "medium",
                "reason": f"Failed payment rate is {failed_payment_rate:.2f}%.",
            })

        if duplicate_invoice_rate > 3:
            risk_flags.append({
                "risk": "duplicate_invoice_risk",
                "severity": "medium",
                "reason": f"Duplicate invoice rate is {duplicate_invoice_rate:.2f}%.",
            })

        if invalid_invoice_rate > 5:
            risk_flags.append({
                "risk": "invalid_invoice_mapping",
                "severity": "high",
                "reason": f"Invalid invoice-order mapping rate is {invalid_invoice_rate:.2f}%.",
            })

        if disputed_invoice_rate > 8:
            risk_flags.append({
                "risk": "high_disputed_invoice_rate",
                "severity": "medium",
                "reason": f"Disputed/rejected invoice rate is {disputed_invoice_rate:.2f}%.",
            })

        return {
            "period": period,
            "row_counts_after_period_filter": {
                "orders": int(len(orders)),
                "payments": int(len(payments)),
                "invoices": int(len(invoices)),
                "refunds": int(len(refunds)),
                "expenses": int(len(expenses)),
            },
            "core_metrics": {
                "total_revenue": round(total_revenue, 2),
                "total_orders": total_orders,
                "total_payments": round(total_payments, 2),
                "total_refunds": round(total_refunds, 2),
                "total_expenses": round(total_expenses, 2),
                "gross_margin": round(gross_margin, 2),
                "gross_margin_percentage": round(gross_margin_percentage, 2),
                "refund_leakage_rate": round(refund_rate, 2),
                "expense_to_revenue_ratio": round(expense_to_revenue_ratio, 2),
                "failed_payment_rate": round(failed_payment_rate, 2),
            },
            "order_value_distribution": {
                "average_order_value": round(avg_order_value, 2),
                "median_order_value": round(median_order_value, 2),
                "standard_deviation": round(std_order_value, 2),
                "p75_order_value": round(p75_order_value, 2),
                "p90_order_value": round(p90_order_value, 2),
                "p95_order_value": round(p95_order_value, 2),
            },
            "invoice_quality_metrics": {
                "total_invoices": int(len(invoices)),
                "duplicate_invoice_count": duplicate_invoice_count,
                "duplicate_invoice_rate": round(duplicate_invoice_rate, 2),
                "invalid_invoice_count": invalid_invoice_count,
                "invalid_invoice_rate": round(invalid_invoice_rate, 2),
                "disputed_invoice_count": disputed_invoice_count,
                "disputed_invoice_rate": round(disputed_invoice_rate, 2),
            },
            "category_revenue": category_revenue.head(10).to_dict(orient="records"),
            "payment_status_mix": payment_mix.to_dict(orient="records"),
            "refund_reason_stats": refund_reason_stats.head(10).to_dict(orient="records"),
            "expense_category_stats": expense_category_stats.head(10).to_dict(orient="records"),
            "invoice_status_mix": invoice_status_mix.to_dict(orient="records"),
            "risk_flags": risk_flags,
            "citations": {
                "sources": [
                    "orders.csv",
                    "payments.csv",
                    "invoices.csv",
                    "refunds.csv",
                    "expenses.csv",
                ]
            },
        }