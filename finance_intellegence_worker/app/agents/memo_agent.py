import json

from app.agents.state import FinanceAgentState
from app.llm.client import LLMClient
from app.llm.prompts import FINANCE_MEMO_SYSTEM_PROMPT


class MemoAgent:
    name = "MemoAgent"

    def run(self, state: FinanceAgentState) -> FinanceAgentState:
        inputs = {
            "user_query": state.user_query,
            "revenue_analysis": state.revenue_analysis,
            "invoice_analysis": state.invoice_analysis,
            "leakage_analysis": state.leakage_analysis,
            "margin_analysis": state.margin_analysis,
        }

        user_prompt = f"""
Create a structured finance action memo from these tool outputs:

{json.dumps(inputs, indent=2, default=str)}
"""

        state.final_memo = LLMClient().generate(
            system_prompt=FINANCE_MEMO_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        return state