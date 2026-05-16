from app.tools.finance_tools import (
    RevenueForecastTool,
    InvoiceMatchingTool,
    LeakageDetectionTool,
    MarginRefundTool,
    FinanceDataValidationTool,
)


class ToolRegistry:
    def __init__(self):
        self.tools = {
            "revenue_forecast_tool": RevenueForecastTool(),
            "invoice_matching_tool": InvoiceMatchingTool(),
            "leakage_detection_tool": LeakageDetectionTool(),
            "margin_refund_tool": MarginRefundTool(),
            "finance_data_validation_tool": FinanceDataValidationTool(),
        }

    def get_tool(self, tool_name: str):
        tool = self.tools.get(tool_name)

        if tool is None:
            raise ValueError(f"Tool not found: {tool_name}")

        return tool

    def list_tools(self):
        return list(self.tools.keys())