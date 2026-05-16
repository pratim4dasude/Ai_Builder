import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class PlannerAgent:
    name = "PlannerAgent"

    ALLOWED_AGENTS = [
        "warehouse_agent",
        "clustering_agent",
        "routing_agent",
        "risk_agent",
        "memo_agent",
    ]

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def plan(self, user_query: str) -> dict:
        prompt = f"""
You are a logistics operations planner.

Your job is to create an execution graph for logistics agents.

Available agents:
1. warehouse_agent
   - checks warehouse allocation
   - inventory
   - stock availability
   - nearest warehouse assignment

2. clustering_agent
   - groups orders by area
   - city
   - zone
   - delivery density

3. routing_agent
   - creates delivery route
   - dispatch route
   - stop optimization

4. risk_agent
   - checks COD risk
   - RTO risk
   - failed delivery risk

5. memo_agent
   - generates final operational memo

Rules:
- memo_agent must ALWAYS be the last step
- risk_agent depends on warehouse_agent because it needs assigned orders
- clustering_agent depends on warehouse_agent
- routing_agent depends on clustering_agent
- memo_agent must always run last
- Do not run risk_agent in parallel with warehouse_agent
- clustering_agent depends on warehouse_agent
- routing_agent depends on clustering_agent
- Select only required agents
- Return valid JSON only
- No markdown
- No explanation outside JSON

User query:
{user_query}

Return JSON format:

{{
  "execution_plan": [
    {{
      "step": 1,
      "parallel": false,
      "agents": ["warehouse_agent"],
      "depends_on": []
    }},
    {{
      "step": 2,
      "parallel": false,
      "agents": ["risk_agent"],
      "depends_on": ["warehouse_agent"]
    }},
    {{
      "step": 3,
      "parallel": false,
      "agents": ["clustering_agent"],
      "depends_on": ["warehouse_agent"]
    }},
    {{
      "step": 4,
      "parallel": false,
      "agents": ["routing_agent"],
      "depends_on": ["clustering_agent"]
    }},
    {{
      "step": 5,
      "parallel": false,
      "agents": ["memo_agent"],
      "depends_on": ["warehouse_agent", "risk_agent", "routing_agent"]
    }}
  ],
  "reason": "short reason"
}}
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a strict JSON logistics planner.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0,
        )

        content = response.choices[0].message.content

        data = json.loads(content)

        execution_plan = data.get("execution_plan", [])

        cleaned_plan = []

        for step in execution_plan:
            valid_agents = [
                agent
                for agent in step.get("agents", [])
                if agent in self.ALLOWED_AGENTS
            ]

            if not valid_agents:
                continue

            cleaned_plan.append(
                {
                    "step": step.get("step"),
                    "parallel": step.get("parallel", False),
                    "agents": valid_agents,
                    "depends_on": step.get("depends_on", []),
                }
            )

        all_agents = []

        for step in cleaned_plan:
            all_agents.extend(step["agents"])

        if "memo_agent" not in all_agents:
            cleaned_plan.append(
                {
                    "step": len(cleaned_plan) + 1,
                    "parallel": False,
                    "agents": ["memo_agent"],
                }
            )

        return {
            "execution_plan": cleaned_plan,
            "reason": data.get(
                "reason",
                "LLM generated execution graph dynamically",
            ),
        }