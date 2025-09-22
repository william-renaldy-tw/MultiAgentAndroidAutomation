# app/orchestrator.py

from typing import Any
from agents.application_selector import ApplicationSelectorAgent
from app.appium_controller import AppiumController
from app.chatroom import ChatRoom
from app.config import settings
from agents.coordinate_extrator import CoordinateExtractorAgent
from agents.chain_of_thought import ChainOfThoughtAgent
from agents.code_generator import CodeGeneratorAgent
from agents.code_verifier import CodeVerifierAgent
from agents.user_prompt_agent import UserPromptAgent
from agents.summarizer import SummarizerAgent
from agents.orchestrator_agent import OrchestratorAgent
from agents.page_summarizer import PageSummarizerAgent

import re
import json
import streamlit as st

from utils.coordinate_utils import annotate_coordinates_from_llm
from utils.sanitizer import sanitize_app_selection, sanitize_code
from utils.history_utils import get_recent_updates


import streamlit as st

def display_latest_agent_message(next_agents: dict):
    """
    Efficiently manages a single UI field that updates with the latest message,
    and provides full message history in a static expander.
    """

    if 'thought_history' not in st.session_state:
        st.session_state.thought_history = []

    if 'message_placeholder' not in st.session_state:
        st.session_state.message_placeholder = st.empty()

    for agent, message in next_agents.items():
        entry = f"[{agent}] {message}"
        if entry not in st.session_state.thought_history:
            st.session_state.thought_history.append(entry)

    latest = st.session_state.thought_history[-1] if st.session_state.thought_history else "Waiting for agent messages..."

    with st.session_state.message_placeholder.container():
        st.markdown("### 🧠 Chain of Thought (Latest)")
        st.info(latest)

        with st.expander("🧾 View Full History", expanded=False):
            for msg in reversed(st.session_state.thought_history):
                st.markdown(f"- {msg}")



agents = [
    CoordinateExtractorAgent(api_key=settings.GOOGLE_API_KEY_COORDINATE),
    ChainOfThoughtAgent(api_key=settings.GOOGLE_API_KEY_COT),
    CodeGeneratorAgent(api_key=settings.GOOGLE_API_KEY_CODEGEN),
    CodeVerifierAgent(api_key=settings.GOOGLE_API_KEY_VERIFIER),
    UserPromptAgent(api_key=settings.GOOGLE_API_KEY_PROMPTER),
    PageSummarizerAgent(api_key=settings.GOOGLE_API_KEY_PAGE_SUMMARIZER),
    SummarizerAgent(api_key=settings.GOOGLE_API_KEY_SUMMARIZER),
    ApplicationSelectorAgent(api_key=settings.GOOGLE_API_KEY_APP_SELECTION),
]

orchestrator_agent = OrchestratorAgent(api_key=settings.GOOGLE_API_KEY_ORCHESTRATOR)


VALID_AGENTS = {
    "CoordinateExtractorAgent",
    "ChainOfThoughtAgent",
    "CodeGeneratorAgent",
    "CodeVerifierAgent",
    "UserPromptAgent",
    "PageSummarizerAgent",
    "SummarizerAgent",
    "ApplicationSelectorAgent"
}

def extract_agent_list(response_text: str) -> dict:
    """
    Extracts a list of agent dicts from structured model output:
    {
      "next_agents": [
        {"name": "Agent1", "expectation": "..."},
        ...
      ]
    }

    Supports:
    - JSON inside triple backticks
    - Fallback: extract names only (without expectations) from plain text

    Returns:
        List of dicts like: [{"name": "AgentX", "expectation": "..."}]
    """


    code_blocks = re.findall(r"```(?:json)?\s*([\s\S]+?)```", response_text, re.IGNORECASE)
    print('================================================================')
    for block in code_blocks:
        try:
            parsed = json.loads(block.strip())
            agents = parsed.get("next_agents", [])
            if isinstance(agents, list):
                result = {}
                for item in agents:
                    if isinstance(item, dict) and item.get("name") in VALID_AGENTS:
                        result[item["name"]] = item.get("expectation", "").strip()
        
                if result:
                    return result
        except json.JSONDecodeError as e:
            print(e)
            continue


    fallback = {}
    for line in response_text.strip().splitlines():
        name = line.strip()
        if name in VALID_AGENTS:
            fallback[name]= ""

    return fallback


def get_latest_by_type(history: list[dict[str, Any]], msg_type: str) -> str | None:
    for msg in reversed(history):
        if msg["type"] == msg_type:
            return msg["content"]
    return None

def run_next_step(chatroom: ChatRoom, driver: AppiumController, time) -> str:
    """
    Ask the OrchestratorAgent which agents should respond next,
    then call them in order.
    
    Returns:
        - "continue": continue to next iteration
        - "done": task complete
        - "wait_user": waiting for user
        - "wait": no agents selected
    """
    try:

        recent_history = get_recent_updates(chatroom.get_history())
        response = orchestrator_agent.generate_response(recent_history)

        chatroom.add_message(
            sender=response["sender"],
            type=response["type"],
            content=response["content"]
        )

        next_agents = extract_agent_list(response["content"])
        agent_names = list(next_agents.keys())
        result_state = "wait"
        print(next_agents)

        display_latest_agent_message(next_agents)

        for agent in agents:
            if agent.name in agent_names:
                try:
                    expectation = next_agents[agent.name]
                    agent_response = agent.generate_response(chatroom.get_history(), expectation)
                    
                    content = agent_response["content"]
                    sender = agent_response.get("sender", agent.name)
                    msg_type = agent_response["type"]

                    
                    chatroom.add_message(
                        sender=sender,
                        type=msg_type,
                        content=content
                    )

                    if agent_response["type"] == "proposed_screen_coordinates":
                        coordinates = annotate_coordinates_from_llm(agent_response["content"], get_latest_by_type(chatroom.get_history(), "screen_image"))
                        print(f"Screen coordinates extracted: {coordinates}")
                        chatroom.add_message(sender="Controller", type="screen_coordinates", content=f"Screen coordinates extracted: {coordinates}")

                    elif agent_response["type"] == "selected_application":
                        app_package_name_with_launchables = agent_response["content"]
                        app_package = sanitize_app_selection(app_package_name_with_launchables)
                        print(f"Application selected: {app_package}")
                        chatroom.add_message("Controller", "feedback", f"Application selected: {app_package}")
                        driver.open_app(app_package)
                        result_state = "continue"


                    elif agent_response["type"] == "code_snippet":
                        last_code = agent_response["content"]
                        cleaned_code = sanitize_code(last_code)
                        print(cleaned_code)
                        try:
                            local_vars = {
                                "driver": driver,
                                "time": time,
                            }
                            exec(cleaned_code, {}, local_vars)
                            prev_error = None
                        except Exception as e:
                            prev_error = str(e)
                            chatroom.add_message("Controller", "error", prev_error)
                            print("Code execution error:", prev_error)
                        result_state = "continue"

                    elif agent_response["type"] == "summary":
                        result_state = "done"
                    elif agent_response["type"] == "user_prompt":
                        result_state = "wait_user"
                    else:
                        result_state = "continue"

                except Exception as e:
                    chatroom.add_message(
                        sender=agent.name,
                        type="error",
                        content=f"Agent error: {str(e)}"
                    )
                    result_state = "continue"

        return result_state

    except Exception as e:
        print(e)
        chatroom.add_message(
            sender="OrchestratorAgent",
            type="error",
            content=f"Orchestrator failed: {e}"
        )
        return "continue"