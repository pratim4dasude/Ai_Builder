import json
from typing import Any, Dict

from openai import OpenAI

from app.config import OPENAI_API_KEY, OPENAI_MODEL, USE_LLM


class LLMService:
    def __init__(self):
        self.enabled = bool(USE_LLM and OPENAI_API_KEY)

        self.client = OpenAI(
            api_key=OPENAI_API_KEY
        ) if self.enabled else None

        self.model = OPENAI_MODEL

    def generate_json(
        self,
        system_prompt: str,
        user_payload: Dict[str, Any],
        fallback: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not self.enabled:
            return fallback

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.4,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": json.dumps(user_payload, default=str),
                    },
                ],
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            return json.loads(content)

        except Exception as error:
            fallback["llm_error"] = str(error)
            fallback["llm_used"] = False
            return fallback

    def generate_text(
        self,
        system_prompt: str,
        user_payload: Dict[str, Any],
        fallback: str,
    ) -> str:
        if not self.enabled:
            return fallback

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.5,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": json.dumps(user_payload, default=str),
                    },
                ],
            )

            return response.choices[0].message.content

        except Exception:
            return fallback