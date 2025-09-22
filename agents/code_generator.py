# agents/code_generator.py

from typing import Any
from agents.base import BaseAgent
from app.config import settings
from utils.sanitizer import sanitize_json

class CodeGeneratorAgent(BaseAgent):
    def __init__(self, api_key: str):
        super().__init__(
            name="CodeGeneratorAgent",
            prompt_key="code_generator",
            api_key=api_key,
            model=settings.DEFAULT_MODEL,
            use_chat=True
        )

    def generate_response(self, history: list[dict[str, Any]], expectation: str) -> dict:
        """
        Generate Selenium Python code based on the page and action plan.
        """
        task = self._get_latest_by_type(history, "task")
        json =  sanitize_json(self._get_latest_by_type(history, "screen_coordinates") or "") or "No JSON extracted"
        action = self._get_latest_by_type(history, "action_plan") or "" + self._get_latest_by_type(history, "agent_selection")  
        page_summary = self._get_latest_by_type(history, "page_summary") or ""
        error = self._get_latest_by_type(history, "error")

        if not all([task, json, action]):
            raise ValueError("Missing required context for code generation.")

        error_section = f"Previous error: {error}" if error else ""

        prompt = self.fill_prompt(
            task=task,
            json=json,
            action=action,
            page_summary=page_summary,
            error_section=error_section,
            expectation=expectation
        )

        code = self.run_chat(prompt)

        return {
            "type": "code_snippet",
            "sender": self.name,
            "content": code.strip()
        }

    def _get_latest_by_type(self, history: list[dict[str, Any]], msg_type: str) -> str | None:
        """Return latest message content of a specific type."""
        for msg in reversed(history):
            if msg["type"] == msg_type:
                return msg["content"]
        return None