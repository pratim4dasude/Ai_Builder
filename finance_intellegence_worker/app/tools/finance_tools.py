from app.tools.base_tool import BaseTool
from app.services.revenue_forecast_service import RevenueForecastService
from app.services.invoice_matching_service import InvoiceMatchingService
from app.services.leakage_detection_service import LeakageDetectionService
from app.services.margin_refund_service import MarginRefundService
from app.services.data_validation import FinanceDataValidationService


class RevenueForecastTool(BaseTool):
    name = "revenue_forecast_tool"
    description = "Analyzes revenue and forecasts next 7 days revenue."

    def run(self):
        return RevenueForecastService().analyze_revenue()


class InvoiceMatchingTool(BaseTool):
    name = "invoice_matching_tool"
    description = "Reconciles invoices with payment records."

    def run(self):
        return InvoiceMatchingService().reconcile_invoices()


class LeakageDetectionTool(BaseTool):
    name = "leakage_detection_tool"
    description = "Detects refund and revenue leakage risk."

    def run(self):
        return LeakageDetectionService().detect_leakage()


class MarginRefundTool(BaseTool):
    name = "margin_refund_tool"
    description = "Analyzes expenses, refunds, and gross margin."

    def run(self):
        return MarginRefundService().analyze_margin()


class FinanceDataValidationTool(BaseTool):
    name = "finance_data_validation_tool"
    description = "Validates required finance CSV files and columns."

    def run(self):
        service = FinanceDataValidationService()
        return {
            "files": service.validate_required_files(),
            "columns": service.validate_columns(),
        }