# agents/page_summarizer.py

from typing import Any
from agents.base import BaseAgent
from app.config import settings
from PIL import Image

class PageSummarizerAgent(BaseAgent):
    def __init__(self, api_key: str):
        super().__init__(
            name="PageSummarizerAgent",
            prompt_key="page_summarizer",
            api_key=api_key,
            model=settings.DEFAULT_IMAGE_READING_MODEL,
            use_chat=False
        )

    def generate_response(self, history: list[dict[str, Any]], expectation: str) -> dict:
        """
        Generate a human-readable summary of everything that happened.
        """
        task = self._get_latest_by_type(history, "task")
        if not task:
            raise ValueError("Missing task for summarization.")

        current_screen = self._get_latest_by_type(history, "screen_image")
        
        if not current_screen:
            raise ValueError("Missing screen image for summarization.")

        prompt = self.fill_prompt(task=task, expectation=expectation)
        summary = self.run_image(prompt, image=Image.open(current_screen))

        return {
            "type": "page_summary",
            "sender": self.name,
            "content": summary.strip()
        }


    def _get_latest_by_type(self, history: list[dict[str, Any]], msg_type: str) -> str | None:
        for msg in reversed(history):
            if msg["type"] == msg_type:
                return msg["content"]
        return None