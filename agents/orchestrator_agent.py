# agents/orchestrator_agent.py

from agents.base import BaseAgent
from app.config import settings


class OrchestratorAgent(BaseAgent):
    def __init__(self, api_key: str):
        super().__init__(
            name="OrchestratorAgent",
            prompt_key="orchestrator_agent",
            api_key=api_key,
            model=settings.DEFAULT_CHAT_MODEL,
            use_chat=True
        )

    def generate_response(self, history: list[dict], expectation: str = "") -> dict:
        """
        Analyze full chat history and return list of agents to activate next.
        Output format: dict with `next_agents` key.
        """
        task = next((msg["content"] for msg in reversed(history) if msg["type"] == "task"), "Unknown task")

        full_history = "\n".join(
            f"[{msg['sender']}] ({msg['type']}): {msg['content']}"
            for msg in history if msg["type"]!="screen_image" 
        )

        prompt = self.fill_prompt(
            task=task,
            history=full_history
        )
        
        response = self.run_chat(prompt)


        return {
            "type": "agent_selection",
            "sender": self.name,
            "content": response.strip()
        }