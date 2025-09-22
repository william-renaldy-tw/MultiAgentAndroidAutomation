# app/config.py

import os
from dotenv import load_dotenv

load_dotenv()

def str_to_bool(val: str, default: bool = False) -> bool:
    return val.lower() in ("1", "true", "yes") if isinstance(val, str) else default

class Settings:
    # === API Keys for Each Agent ===
    GOOGLE_API_KEY_COORDINATE: str = os.getenv("GOOGLE_API_KEY_COORDINATE", "")
    GOOGLE_API_KEY_COT: str = os.getenv("GOOGLE_API_KEY_COT", "")
    GOOGLE_API_KEY_CODEGEN: str = os.getenv("GOOGLE_API_KEY_CODEGEN", "")
    GOOGLE_API_KEY_VERIFIER: str = os.getenv("GOOGLE_API_KEY_VERIFIER", "")
    GOOGLE_API_KEY_SUMMARIZER: str = os.getenv("GOOGLE_API_KEY_SUMMARIZER", "")
    GOOGLE_API_KEY_PROMPTER: str = os.getenv("GOOGLE_API_KEY_PROMPTER", "")
    GOOGLE_API_KEY_ORCHESTRATOR = os.getenv("GOOGLE_API_KEY_ORCHESTRATOR", "")
    GOOGLE_API_KEY_PAGE_SUMMARIZER = os.getenv("GOOGLE_API_KEY_PAGE_SUMMARIZER", "")
    GOOGLE_API_KEY_APP_SELECTION = os.getenv("GOOGLE_API_KEY_APP_SELECTION", "")
    GOOGLE_API_KEY_TOKENIZER = os.getenv("GOOGLE_API_KEY_TOKENIZER", "")
    
    # === Default Models ===
    DEFAULT_MODEL: str = "gemini-2.0-flash"
    DEFAULT_CHAT_MODEL: str = "gemini-2.0-flash"
    DEFAULT_IMAGE_EXTRACTION_MODEL: str = "gemini-2.5-pro"
    DEFAULT_IMAGE_READING_MODEL: str = "gemini-2.5-flash"

    # === Runtime Parameters ===
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", 10))
    DEBUG_MODE: bool = str_to_bool(os.getenv("DEBUG_MODE", "0"))

    # === Browser Settings ===
    EDGE_PROFILE_PATH: str = os.getenv("EDGE_PROFILE_PATH", "")
    EDGE_PROFILE_NAME: str = os.getenv("EDGE_PROFILE_NAME", "Default")

    # === Misc Paths ===
    PROMPT_DIR: str = os.getenv("PROMPT_DIR", "prompts/")
    LOG_DIR: str = os.getenv("LOG_DIR", "logs/")
    MACRO_DIR: str = os.getenv("MACRO_DIR", "macros/saved/")
    SUMMARY_DIR: str = os.getenv("SUMMARY_DIR", "data/summaries/")
    TRANSCRIPT_DIR: str = os.getenv("TRANSCRIPT_DIR", "data/transcripts/")

    # === Appium Settings ===
    APPIUM_SERVER_URL: str = os.getenv("APPIUM_SERVER_URL", "http://localhost:4723")

    def validate(self):
        required_keys = {
            "GOOGLE_API_KEY_COORDINATE": self.GOOGLE_API_KEY_COORDINATE,
            "GOOGLE_API_KEY_COT": self.GOOGLE_API_KEY_COT,
            "GOOGLE_API_KEY_CODEGEN": self.GOOGLE_API_KEY_CODEGEN,
            "GOOGLE_API_KEY_VERIFIER": self.GOOGLE_API_KEY_VERIFIER
        }
        for key, val in required_keys.items():
            if not val:
                print(f"Warning: Missing environment variable for {key}")

settings = Settings()