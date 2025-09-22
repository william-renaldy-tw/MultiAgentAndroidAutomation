# agents/summarizer.py

from typing import Any
from agents.base import BaseAgent
from app.config import settings

class SummarizerAgent(BaseAgent):
    def __init__(self, api_key: str):
        super().__init__(
            name="SummarizerAgent",
            prompt_key="summarizer",
            api_key=api_key,
            model=settings.DEFAULT_CHAT_MODEL,
            use_chat=True
        )

    def generate_response(self, history: list[dict[str, Any]], expectation: str) -> dict:
        """
        Generate a human-readable summary of everything that happened.
        """
        task = self._get_latest_by_type(history, "task")
        if not task:
            raise ValueError("Missing task for summarization.")

        full_history = "\n".join(
            f"[{msg['sender']}] ({msg['type']}): {msg['content']}"
            for msg in history if msg["type"]!="screen_image" 
        )

        prompt = self.fill_prompt(task=task, history = full_history, expectation=expectation)   
        summary = self.run_chat(prompt)

        return {
            "type": "summary",
            "sender": self.name,
            "content": summary.strip()
        }

    def _get_latest_by_type(self, history: list[dict[str, Any]], msg_type: str) -> str | None:
        for msg in reversed(history):
            if msg["type"] == msg_type:
                return msg["content"]
        return None