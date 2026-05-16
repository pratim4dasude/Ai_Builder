import json

from app.agents.state import FinanceAgentState
from app.llm.client import LLMClient
from app.llm.prompts import FINANCE_MEMO_SYSTEM_PROMPT


class MemoAgent:
    name = "MemoAgent"

    def run(self, state: FinanceAgentState) -> FinanceAgentState:
        inputs = {
            "user_query": state.user_query,
            "period": state.period,
            "revenue_analysis": state.revenue_analysis,
            "invoice_analysis": state.invoice_analysis,
            "leakage_analysis": state.leakage_analysis,
            "margin_analysis": state.margin_analysis,
            "statistics_analysis": state.statistics_analysis,
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

        Structured tool outputs:
        {json.dumps(inputs, indent=2, default=str)}
        """

        state.final_memo = LLMClient().generate(
            system_prompt=FINANCE_MEMO_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        return state