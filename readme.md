# PoC-AndroidAutomationVisual

**Proof of Concept** for automating Android applications using a multi-agent, visual-automation architecture powered by the Gemini API (Google), Appium and Selenium.

This repository demonstrates how several specialized agents (orchestration, visual coordinate extraction, code generation & verification, page summarization and user prompting) can cooperate to inspect app screens (via screenshots), plan actions, generate Appium automation code and run it on a connected Android device/emulator.

---

## Key Features

* Multi-agent orchestration driven by an `OrchestratorAgent` that chooses which agent takes the next step.
* Visual element / coordinate extraction from screenshots so automation can act on visible UI elements rather than relying purely on accessibility ids.
* LLM-assisted code generation for Appium-based interaction and a verifier agent to check generated code.
* Streamlit UI for monitoring the automation and an Appium-backed controller to actually execute on-device actions.
* Debugging support: chatroom history is saved to `debug_chatroom.json` for offline review.

---

## Requirements & Prerequisites

* Python 3.10+ (tested with 3.11 in the repo environment)
* `pip` for installing Python dependencies
* Appium server installed and accessible (default URL: `http://localhost:4723`)
* Android SDK platform tools (for `adb`) and at least one connected Android device or running emulator
* A Google Gemini API key (various agent keys described below). The project expects separate keys per agent role (see `.env` below).

---

## Pre-Setup

Before running this project, please follow the pre-setup instructions provided in the following documents:

* [Pre-Setup Guide 1](https://docs.google.com/document/d/e/2PACX-1vRnTmwDeynRlYUu9ib-jtkH7Ukas7TWyd0ww-aS6itEKjhXWCaGeI72fJ_0MIwrHG4oCK140Iv7iwBy/pub#h.eoqr2a4ylhfk)
* [Pre-Setup Guide 2](https://docs.google.com/document/d/e/2PACX-1vTr6um5UChhTQhdwHX73uYKGOT2h7lOyKHxlCPWHuOXs42FEvaT_GAvlTocTL_f_UaHkcDZntcZPO9f/pub)

These guides cover all necessary environment and dependency configurations.

---

## .env (example)

Create a `.env` file at the repository root. The project expects a number of environment variables (API keys and runtime settings). Example template:

```ini
# Gemini / Google GenAI keys (one key per agent role)
GOOGLE_API_KEY_COORDINATE=
GOOGLE_API_KEY_COT=
GOOGLE_API_KEY_CODEGEN=
GOOGLE_API_KEY_VERIFIER=
GOOGLE_API_KEY_SUMMARIZER=
GOOGLE_API_KEY_PROMPTER=
GOOGLE_API_KEY_ORCHESTRATOR=
GOOGLE_API_KEY_PAGE_SUMMARIZER=
GOOGLE_API_KEY_APP_SELECTION=
GOOGLE_API_KEY_TOKENIZER=

# How many iterations the orchestrator should attempt before giving up
MAX_ITERATIONS=20
```

> You can obtain Gemini/API keys from Google AI Studio (e.g. [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)). Ensure the keys you provision have the required access for the models you intend to use.

---

## Installation

1. Clone this repository:

```bash
git clone https://github.com/william-renaldy-tw/MultiAgentAndroidAutomation.git
cd PoC-AndroidAutomationVisual
```

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Make sure Appium is installed and running. You can start Appium with:

```bash
appium
```
---

## Running the project

You can run the Streamlit app directly:

```bash
streamlit run app/main.py
```

---

## Project structure (high level)

* `agents/` — agent implementations (each agent is a small class that prepares prompts, calls Gemini and returns structured messages):

  * `application_selector.py` — chooses which installed app to run or analyze (uses ADB to list installed packages).
  * `coordinate_extractor.py` — inspects screenshots, creates grid overlays and proposes screen coordinates/actions.
  * `chain_of_thought.py` — maintains an internal chain-of-thought trace used by other agents.
  * `code_generator.py` — generates Appium Python code to perform a planned action.
  * `code_verifier.py` — verifies or sanitizes LLM-generated code snippets.
  * `user_prompt_agent.py` — asks the user for missing inputs (e.g., credentials, manual steps) when automation cannot proceed.
  * `summarizer.py` and `page_summarizer.py` — summarize page content and overall results for the user.
  * `orchestrator_agent.py` — the central decision-maker that triggers which agent should run next.

* `app/` — orchestration and UI glue:

  * `appium_controller.py` — helper for sending commands to Appium / device.
  * `orchestrator.py` and `controller.py` — the primary automation loop that runs agent cycles and executes generated actions.
  * `chatroom.py` — in-memory message exchange between agents and logging/debug output.
  * `main.py` — Streamlit app UI for monitoring the automation in real time.
  * `config.py` — environment variable loader and project settings.

* `prompts/` — YAML prompt templates for each agent describing roles, instructions and constraints used when calling the LLM.

* `utils/` — small utility helpers:

  * `driver_utils.py` — uses `adb` to list installed packages.
  * `sanitizer.py` — cleans code/JSON generated by LLMs.
  * `coordinate_utils.py`, `image_utils.py`, etc. (utilities used by visual-extraction and app control).
  * `cleanup.py` - clears the screenshots taken during the process.

* `requirements.txt` — Python dependencies.


---

## How the multi-agent flow works (overview)

1. The `OrchestratorAgent` along with `ChainOfThoughtAgent` decides which agent should act next, based on the task description and recent history.
2. If the orchestrator requests a screen understanding step, `CoordinateExtractorAgent` and/or `PageSummarizerAgent` will analyze the latest screenshot.
3. When an action is required, `CodeGeneratorAgent` produces Appium/Python snippets that the system can execute.
4. `CodeVerifierAgent` checks and sanitizes generated code before execution.
5. `AppiumController` executes safe, verified commands on the connected Android device.
6. `SummarizerAgent` produces a final human-friendly summary of what was performed.

The system also includes `UserPromptAgent` to request inputs from the user when automation is blocked (e.g., login required, CAPTCHA, permissions popups that require manual interaction).

---

## Debugging & Logging

* The controller saves the chatroom's history to `debug_chatroom.json` after a task run. This is very useful for replaying the multi-agent conversation and for debugging generated code.
* If automation seems to stall:

  * Verify the Appium server is running and reachable at `APPIUM_SERVER_URL`.
  * Verify `adb devices` lists your device/emulator and it is authorized.
  * Check that the `.env` contains the required Gemini API keys.
  * Inspect Streamlit UI (if running) for agent messages, chain-of-thought and the latest screenshot.