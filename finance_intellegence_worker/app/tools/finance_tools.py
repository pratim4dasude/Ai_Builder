from app.tools.base_tool import BaseTool
from app.services.revenue_forecast_service import RevenueForecastService
from app.services.invoice_matching_service import InvoiceMatchingService
from app.services.leakage_detection_service import LeakageDetectionService
from app.services.margin_refund_service import MarginRefundService
from app.services.data_validation import FinanceDataValidationService
from app.services.statistics_service import StatisticsService


class RevenueForecastTool(BaseTool):
    name = "revenue_forecast_tool"
    description = "Analyzes revenue and forecasts next 7 days revenue."

    def run(self, period=None):
        return RevenueForecastService().analyze_revenue(period=period)


class InvoiceMatchingTool(BaseTool):
    name = "invoice_matching_tool"
    description = "Reconciles invoices with payment records."

    def run(self, period=None):
        return InvoiceMatchingService().reconcile_invoices(period=period)


class LeakageDetectionTool(BaseTool):
    name = "leakage_detection_tool"
    description = "Detects refund and revenue leakage risk."

    def run(self, period=None):
        return LeakageDetectionService().detect_leakage(period=period)


class MarginRefundTool(BaseTool):
    name = "margin_refund_tool"
    description = "Analyzes expenses, refunds, and gross margin."

    def run(self, period=None):
        return MarginRefundService().analyze_margin(period=period)


class FinanceDataValidationTool(BaseTool):
    name = "finance_data_validation_tool"
    description = "Validates required finance CSV files and columns."

    def run(self, period=None):
        service = FinanceDataValidationService()
        return {
            "files": service.validate_required_files(),
            "columns": service.validate_columns(),
        }


class StatisticsTool(BaseTool):
    name = "statistics_tool"
    description = "Calculates finance statistics, risk flags, distributions, and anomaly signals."

    def run(self, period=None):
        return StatisticsService().analyze_statistics(period=period)