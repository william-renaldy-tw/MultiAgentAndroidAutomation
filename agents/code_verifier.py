# agents/code_verifier.py

from typing import Any
from agents.base import BaseAgent
from app.config import settings
from utils.sanitizer import sanitize_json, sanitize_code

class CodeVerifierAgent(BaseAgent):
    def __init__(self, api_key: str):
        super().__init__(
            name="CodeVerifierAgent",
            prompt_key="code_verifier",
            api_key=api_key,
            model=settings.DEFAULT_CHAT_MODEL, 
            use_chat=False
        )

    def generate_response(self, history: list[dict[str, Any]], expectation: str) -> dict:
        """
        Improve the existing code snippet using error + context.
        """
        task = self._get_latest_by_type(history, "task")
        json = sanitize_json(self._get_latest_by_type(history, "screen_coordinates")) or "No JSON extracted"
        action = self._get_latest_by_type(history, "action_plan")
        page_summary = self._get_latest_by_type(history, "page_summary") or ""
        code = sanitize_code(self._get_latest_by_type(history, "code_snippet"))
        error = self._get_latest_by_type(history, "error")

        if not all([task, json, action, code]):
            raise ValueError("Missing context for code verification.")

        error_section = f"Previous error: {error}" if error else ""

        prompt = self.fill_prompt(
            task=task,
            json=json,
            action=action,
            code=code,
            error=error_section,
            page_summary=page_summary,
            expectation=expectation
        )

        verified_code = self.run_generate(prompt)

        return {
            "type": "code_snippet",
            "sender": self.name,
            "content": verified_code.strip()
        }

    def _get_latest_by_type(self, history: list[dict[str, Any]], msg_type: str) -> str | None:
        """Return latest message content of a specific type."""
        for msg in reversed(history):
            if msg["type"] == msg_type:
                return msg["content"]
        return None