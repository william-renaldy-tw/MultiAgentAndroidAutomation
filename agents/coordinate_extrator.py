# agents/coordinate_extractor.py

from PIL import Image
from typing import Any
from agents.base import BaseAgent
from app.config import settings
from utils.coordinate_utils import create_grid_overlay, grid_to_coordinates, sanitize_grid_coordinates, replace_json_with_coordinates


class CoordinateExtractorAgent(BaseAgent):
    def __init__(self, api_key: str):
        super().__init__(
            name="CoordinateExtractorAgent",
            prompt_key="coordinate_extractor",
            api_key=api_key,
            model=settings.DEFAULT_IMAGE_EXTRACTION_MODEL,
            use_chat=False 
        )

    def generate_response(self, history: list[dict[str, Any]], expectation: str) -> dict:
        """
        Generate the required coordinates based on the current screen image and task.
        """
        task = self._get_latest_by_type(history, "task")
        screen_image = self._get_latest_by_type(history, "screen_image")
        page_summary = self._get_latest_by_type(history, "page_summary") or ""

        grid_data = create_grid_overlay(screen_image)
        

        if not task or not screen_image:
            raise ValueError("Missing task or screen image in history.")
        
        filled_prompt = self.fill_prompt(
            task=task, expectation=expectation,
            page_summary=page_summary
        )

        extracted = self.run_image(filled_prompt, image=Image.open(grid_data["grid_image_path"]))

        cell_number = sanitize_grid_coordinates(extracted)

        coordinates = grid_to_coordinates(cell_numbers=cell_number, grid_data=grid_data)

        response = replace_json_with_coordinates(extracted, coordinates, cell_number)

        return {
            "type": "proposed_screen_coordinates",
            "sender": self.name,
            "content": response.strip()
        }

    def _get_latest_by_type(self, history: list[dict[str, Any]], msg_type: str) -> str | None:
        """Return latest message content of a specific type."""
        for msg in reversed(history):
            if msg["type"] == msg_type:
                return msg["content"]
        return None