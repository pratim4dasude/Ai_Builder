from typing import Any, Dict

from app.agents.state import FinanceAgentState
from app.utils.json_cleaner import clean_json


def build_finance_response(state: FinanceAgentState) -> Dict[str, Any]:
    revenue = state.revenue_analysis or {}
    leakage = state.leakage_analysis or {}
    margin = state.margin_analysis or {}
    statistics = state.statistics_analysis or {}

    core_metrics = statistics.get("core_metrics", {})
    invoice_quality = statistics.get("invoice_quality_metrics", {})
    risk_flags = statistics.get("risk_flags", [])

    summary = {
        "finance_status": extract_finance_status(state.final_memo),
        "period": state.period,
        "total_revenue": core_metrics.get("total_revenue", revenue.get("total_revenue")),
        "total_orders": core_metrics.get("total_orders", revenue.get("total_orders")),
        "avg_order_value": revenue.get("avg_order_value"),
        "forecast_next_7_days": revenue.get("forecast_next_7_days"),
        "forecast_method": revenue.get("forecast_method"),
        "refund_leakage_rate": core_metrics.get(
            "refund_leakage_rate",
            leakage.get("leakage_percentage"),
        ),
        "gross_margin": core_metrics.get("gross_margin", margin.get("gross_margin")),
        "gross_margin_percentage": core_metrics.get(
            "gross_margin_percentage",
            margin.get("margin_percentage"),
        ),
        "failed_payment_rate": core_metrics.get("failed_payment_rate"),
        "invalid_invoice_rate": invoice_quality.get("invalid_invoice_rate"),
        "risk_flags_count": len(risk_flags),
        "high_risk_flags": [
            flag for flag in risk_flags
            if str(flag.get("severity", "")).lower() == "high"
        ],
    }

    response = {
        "answer": state.final_memo,
        "summary": summary,
        "agents": {
            "selected_agents": state.selected_agents,
            "execution_plan": state.execution_plan,
            "metadata": state.metadata,
        },
        "data": {
            "revenue_analysis": state.revenue_analysis,
            "invoice_analysis": state.invoice_analysis,
            "leakage_analysis": state.leakage_analysis,
            "margin_analysis": state.margin_analysis,
            "statistics_analysis": state.statistics_analysis,
        },
        "provenance": {
            "revenue": revenue.get("citations"),
            "invoice": (state.invoice_analysis or {}).get("citations"),
            "leakage": (state.leakage_analysis or {}).get("citations"),
            "margin": (state.margin_analysis or {}).get("citations"),
            "statistics": (state.statistics_analysis or {}).get("citations"),
        },
        "debug": {
            "session_id": state.session_id,
            "query": state.user_query,
            "errors": state.errors,
        },
    }

    return clean_json(response)


def build_stream_final_response(state: FinanceAgentState) -> Dict[str, Any]:
    revenue = state.revenue_analysis or {}
    leakage = state.leakage_analysis or {}
    margin = state.margin_analysis or {}
    statistics = state.statistics_analysis or {}

    core_metrics = statistics.get("core_metrics", {})
    invoice_quality = statistics.get("invoice_quality_metrics", {})
    risk_flags = statistics.get("risk_flags", [])

    response = {
        "answer": state.final_memo,
        "summary": {
            "finance_status": extract_finance_status(state.final_memo),
            "period": state.period,
            "total_revenue": core_metrics.get("total_revenue", revenue.get("total_revenue")),
            "forecast_next_7_days": revenue.get("forecast_next_7_days"),
            "forecast_method": revenue.get("forecast_method"),
            "refund_leakage_rate": core_metrics.get(
                "refund_leakage_rate",
                leakage.get("leakage_percentage"),
            ),
            "gross_margin_percentage": core_metrics.get(
                "gross_margin_percentage",
                margin.get("margin_percentage"),
            ),
            "invalid_invoice_rate": invoice_quality.get("invalid_invoice_rate"),
            "risk_flags_count": len(risk_flags),
        },
        "agents": {
            "selected_agents": state.selected_agents,
            "execution_plan": state.execution_plan,
        },
        "errors": state.errors,
    }

    return clean_json(response)


def extract_finance_status(memo: str | None) -> str | None:
    if not memo:
        return None

    memo_lower = memo.lower()

    if "overall finance status: high risk" in memo_lower:
        return "high risk"

    if "overall finance status: watchlist" in memo_lower:
        return "watchlist"

    if "overall finance status: healthy" in memo_lower:
        return "healthy"

    if "high risk" in memo_lower:
        return "high risk"

    if "watchlist" in memo_lower:
        return "watchlist"

    if "healthy" in memo_lower:
        return "healthy"

    return None