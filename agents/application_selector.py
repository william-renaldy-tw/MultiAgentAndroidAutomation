# agents/application_selector.py

from typing import Any
from agents.base import BaseAgent
from app.config import settings
from utils.driver_utils import get_installed_packages

class ApplicationSelectorAgent(BaseAgent):
    def __init__(self, api_key: str):
        self.available_apps = get_installed_packages()
        super().__init__(
            name="ApplicationSelectorAgent",
            prompt_key="application_selector",
            api_key=api_key,
            model=settings.DEFAULT_CHAT_MODEL,
            use_chat=True
        )

    def generate_response(self, history: list[dict[str, Any]], expectation: str) -> dict:
        """
        Analyze the task.
        Return the suitable application.
        """
        task = self._get_latest_by_type(history, "task")
        feedback = self._get_latest_by_type(history, "feedback")
        error = self._get_latest_by_type(history, "error")

        if not task:
            raise ValueError("Missing required context: task")

        feedback_section = ""
        if feedback:
            feedback_section += f"Previous feedback: {feedback}\n"
        if error:
            feedback_section += f"Previous error: {error}\n"

        prompt = self.fill_prompt(
            task=task,
            available_apps=self.available_apps,
            feedback_section=feedback_section,
            expectation=expectation
        )

        response = self.run_chat(prompt)

        return {
            "type": "selected_application",
            "sender": self.name,
            "content": response.strip()
        }

    def _get_latest_by_type(self, history: list[dict[str, Any]], msg_type: str) -> str | None:
        """Return latest message content of a specific type."""
        for msg in reversed(history):
            if msg["type"] == msg_type:
                return msg["content"]
        return None