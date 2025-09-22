# app/chatroom.py

from datetime import datetime, timezone
from typing import List, Optional

class ChatRoom:
    """
    A simple message bus that stores agent/system/user messages in memory.
    Supports timestamping, filtering, and traceability.
    """
    def __init__(self):
        self.messages: List[dict] = []

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def add_message(self, sender: str, type: str, content: str) -> None:
        """
        Add a message to the chatroom.

        Args:
            sender (str): Who sent the message (agent name, "user", etc.)
            type (str): Message type (e.g. "task", "screen content", "code_snippet")
            content (str): Actual message payload
        """
        self.messages.append({
            "sender": sender,
            "type": type,
            "content": content,
            "timestamp": self._timestamp()
        })

    def get_history(self) -> List[dict]:
        """Return full message history (FIFO)."""
        return self.messages

    def get_latest(self, msg_type: str) -> Optional[dict]:
        """Return latest message of a given type."""
        for msg in reversed(self.messages):
            if msg["type"] == msg_type:
                return msg
        return None

    def filter_by_type(self, msg_type: str) -> List[dict]:
        """Return list of all messages matching the given type."""
        return [msg for msg in self.messages if msg["type"] == msg_type]

    def has_type_from_sender(self, msg_type: str, sender: str) -> bool:
        """Check if any message matches given type and sender."""
        return any(msg["type"] == msg_type and msg["sender"] == sender for msg in self.messages)

    def clear(self) -> None:
        """Clear all stored messages."""
        self.messages = []

    def __repr__(self) -> str:
        return f"<ChatRoom with {len(self.messages)} messages>"