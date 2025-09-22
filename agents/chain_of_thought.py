# agents/chain_of_thought.py

from typing import Any
from agents.base import BaseAgent
from app.config import settings

class ChainOfThoughtAgent(BaseAgent):
    def __init__(self, api_key: str):
        super().__init__(
            name="ChainOfThoughtAgent",
            prompt_key="chain_of_thought",
            api_key=api_key,
            model=settings.DEFAULT_CHAT_MODEL,
            use_chat=True
        )

    def generate_response(self, history: list[dict[str, Any]], expectation: str) -> dict:
        """
        Analyze the task.
        Return the next best action.
        """
        task = self._get_latest_by_type(history, "task")
        json = self._get_latest_by_type(history, "screen_coordinates") or "No JSON data found."
        feedback = self._get_latest_by_type(history, "feedback")
        page_summary = self._get_latest_by_type(history, "page_summary") or ""
        error = self._get_latest_by_type(history, "error")

        if not task or not json:
            raise ValueError("Missing required context: task or screen_coordinates.")

        feedback_section = ""
        if feedback:
            feedback_section += f"Previous feedback: {feedback}\n"
        if error:
            feedback_section += f"Previous error: {error}\n"

        prompt = self.fill_prompt(
            task=task,
            json=json,
            feedback_section=feedback_section,
            expectation=expectation,
            page_summary=page_summary
        )

        response = self.run_chat(prompt)

        return {
            "type": "action_plan",
            "sender": self.name,
            "content": response.strip()
        }

    def _get_latest_by_type(self, history: list[dict[str, Any]], msg_type: str) -> str | None:
        """Return latest message content of a specific type."""
        for msg in reversed(history):
            if msg["type"] == msg_type:
                return msg["content"]
        return None