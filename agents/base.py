# agents/base.py

import os
import yaml
from abc import ABC, abstractmethod
from typing import Any
from app.config import settings
from google import genai
from google.genai import types
from PIL import ImageFile
from pydantic import TypeAdapter

# Load prompt templates
PROMPTS = {}
for filename in os.listdir(settings.PROMPT_DIR):
    if filename.endswith(".yaml") or filename.endswith(".yml"):
        prompt_key = os.path.splitext(filename)[0]
        with open(os.path.join(settings.PROMPT_DIR, filename), "r") as f:
            print(f"Loading prompt template: {filename}")
            PROMPTS[prompt_key] = yaml.safe_load(f)


class BaseAgent(ABC):
    def __init__(self, name: str, prompt_key: str, api_key: str, model: str = settings.DEFAULT_MODEL, use_chat: bool = True):
        self.name = name
        self.prompt_key = prompt_key
        self.api_key = api_key
        self.model_id = model
        self.use_chat = use_chat
        self.prompt_template = PROMPTS[prompt_key]["prompt"]
        self.system_instruction = PROMPTS[prompt_key].get("system")

        # Gemini client setup
        self.client = genai.Client(api_key=self.api_key)
        self.chat = None

        if self.use_chat:
            config = types.GenerateContentConfig()
            if self.system_instruction:
                config.system_instruction = self.system_instruction
            self.chat = self.client.chats.create(
                model=self.model_id,
                config=config
            )

    def fill_prompt(self, **kwargs) -> str:
        """Fill the prompt template using task-specific values."""
        return self.prompt_template.format(**kwargs)

    def run_chat(self, message: str) -> str:
        """Send a message using chat interface."""
        if not self.chat:
            raise ValueError("Chat mode not initialized.")
        response = self.chat.send_message(message)
        return response.text

    def run_generate(self, message: str) -> str:
        """Send a one-shot generation request (stateless)."""
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=message,
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction
            ) if self.system_instruction else None
        )
        return response.text

    def run_image(self, message: str, image: ImageFile) -> str:
        """Send a one-shot generation request (stateless)."""
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=[message, image],
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction
            ) if self.system_instruction else None
        )
        return response.text

    def count_tokens(self, message: str) -> int:
        """Count tokens before sending a request (optional for trimming)."""
        response = self.client.models.count_tokens(
            model=self.model_id,
            contents=message
        )
        return response.total_tokens
    
    
    @abstractmethod
    def generate_response(self, history: list[dict[str, Any]], expectation: str) -> dict:
        pass