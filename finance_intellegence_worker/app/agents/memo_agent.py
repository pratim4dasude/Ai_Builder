import json

from app.agents.state import FinanceAgentState
from app.llm.client import LLMClient
from app.llm.prompts import FINANCE_MEMO_SYSTEM_PROMPT


class MemoAgent:
    name = "MemoAgent"

    def run(self, state: FinanceAgentState) -> FinanceAgentState:
        finance_decision = self._calculate_finance_decision(state)

        inputs = {
            "user_query": state.user_query,
            "period": state.period,
            "revenue_analysis": state.revenue_analysis,
            "invoice_analysis": state.invoice_analysis,
            "leakage_analysis": state.leakage_analysis,
            "margin_analysis": state.margin_analysis,
            "statistics_analysis": state.statistics_analysis,
            "finance_decision": finance_decision,
            "errors": state.errors,
        }

        user_prompt = f"""
Create a CFO-style finance intelligence memo using ONLY these tool outputs.

Important:
- Copy numbers exactly from the tool outputs.
- Do not invent or modify numbers.
- Use ₹ / INR for money.
- You MUST include a section named "## 3. Revenue Forecast" if revenue_analysis.forecast_method exists.
- If XGBoost forecast is present, include forecast_method, forecast_next_7_days, daily_forecast, mae, mape, train_days, and test_days.
- If risk_flags are present, prioritize them in Recommended Actions.
- The final decision MUST use the provided finance_decision object.
- Do not override finance_decision.status.
- Do not end with only one word like "Healthy".
- Final Decision must explain why that status was chosen.

Structured tool outputs:
{json.dumps(inputs, indent=2, default=str)}
"""

        try:
            state.final_memo = LLMClient().generate(
                system_prompt=FINANCE_MEMO_SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )

        except Exception as e:
            state.errors.append(f"{self.name} failed: {str(e)}")
            state.final_memo = self._fallback_memo(state, finance_decision)

        return state

    def _calculate_finance_decision(self, state: FinanceAgentState) -> dict:
        statistics = state.statistics_analysis or {}
        core_metrics = statistics.get("core_metrics", {})
        invoice_quality = statistics.get("invoice_quality_metrics", {})
        risk_flags = statistics.get("risk_flags", [])

        margin_analysis = state.margin_analysis or {}

        margin_percentage = core_metrics.get(
            "gross_margin_percentage",
            margin_analysis.get("margin_percentage")
        )

        refund_leakage_rate = core_metrics.get("refund_leakage_rate")
        failed_payment_rate = core_metrics.get("failed_payment_rate")
        invalid_invoice_rate = invoice_quality.get("invalid_invoice_rate")
        disputed_invoice_rate = invoice_quality.get("disputed_invoice_rate")

        high_risk_count = sum(
            1 for flag in risk_flags
            if str(flag.get("severity", "")).lower() == "high"
        )

        medium_risk_count = sum(
            1 for flag in risk_flags
            if str(flag.get("severity", "")).lower() == "medium"
        )

        reasons = []

        status = "healthy"

        if margin_percentage is not None and margin_percentage < 15:
            status = "high risk"
            reasons.append(f"Gross margin percentage is {margin_percentage}, below the safe threshold.")

        if refund_leakage_rate is not None and refund_leakage_rate > 8:
            if status == "healthy":
                status = "watchlist"
            reasons.append(f"Refund leakage rate is {refund_leakage_rate}, above the 8% threshold.")

        if invalid_invoice_rate is not None and invalid_invoice_rate > 40:
            status = "high risk"
            reasons.append(f"Invalid invoice rate is {invalid_invoice_rate}, above the 40% threshold.")

        if failed_payment_rate is not None and failed_payment_rate > 8:
            if status == "healthy":
                status = "watchlist"
            reasons.append(f"Failed payment rate is {failed_payment_rate}, above the 8% threshold.")

        if disputed_invoice_rate is not None and disputed_invoice_rate > 8:
            if status == "healthy":
                status = "watchlist"
            reasons.append(f"Disputed invoice rate is {disputed_invoice_rate}, above the 8% threshold.")

        if high_risk_count >= 2:
            status = "high risk"
            reasons.append(f"There are {high_risk_count} high-severity risk flags.")

        if not reasons:
            reasons.append("Revenue, margin, leakage, invoice and payment indicators are within acceptable range.")

        return {
            "status": status,
            "reasons": reasons,
            "high_risk_count": high_risk_count,
            "medium_risk_count": medium_risk_count,
            "decision_rule": {
                "healthy": "No major risk indicators detected.",
                "watchlist": "Business is stable but one or more risk indicators need monitoring.",
                "high_risk": "Major finance risks are present and require immediate action.",
            },
        }

    def _fallback_memo(self, state: FinanceAgentState, finance_decision: dict) -> str:
        revenue = state.revenue_analysis or {}
        statistics = state.statistics_analysis or {}
        core_metrics = statistics.get("core_metrics", {})

        return f"""
# Finance Intelligence Memo

## 1. Executive Summary
- Finance analysis completed for the selected period.
- Total revenue: ₹{core_metrics.get("total_revenue", revenue.get("total_revenue"))}
- Gross margin percentage: {core_metrics.get("gross_margin_percentage")}
- Refund leakage rate: {core_metrics.get("refund_leakage_rate")}
- Final finance status: {finance_decision.get("status")}

## 2. Final Decision
Overall finance status is **{finance_decision.get("status")}**.

Reasons:
{chr(10).join(f"- {reason}" for reason in finance_decision.get("reasons", []))}
"""