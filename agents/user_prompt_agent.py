# agents/user_prompt_agent.py

from typing import Any
from agents.base import BaseAgent
from app.config import settings

class UserPromptAgent(BaseAgent):
    def __init__(self, api_key: str):
        super().__init__(
            name="UserPromptAgent",
            prompt_key="user_prompt_agent",
            api_key=api_key,
            model=settings.DEFAULT_CHAT_MODEL,
            use_chat=True
        )

    def generate_response(self, history: list[dict[str, Any]], expectation: str) -> dict:
        """
        Generate a message to prompt the user for help/input.
        """
        task = self._get_latest_by_type(history, "task")
        json = self._get_latest_by_type(history, "screen_coordinates") or "No JSON extracted"
        page_summary = self._get_latest_by_type(history, "page_summary") or ""
        error = self._get_latest_by_type(history, "error") or self._get_latest_by_type(history, "agent_selection")

        if not all([task, json, error]):
            raise ValueError("Missing task, JSON, or error context for user prompt.")

        prompt = self.fill_prompt(
            task=task,
            json=json,
            error=error,
            expectation=expectation,
            page_summary=page_summary
        )

        message = self.run_chat(prompt)

        return {
            "type": "user_prompt",
            "sender": self.name,
            "content": message.strip()
        }

    def _get_latest_by_type(self, history: list[dict[str, Any]], msg_type: str) -> str | None:
        for msg in reversed(history):
            if msg["type"] == msg_type:
                return msg["content"]
        return None