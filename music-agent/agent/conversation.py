"""ConversationHistory — Multi-turn message memory for agent."""

from typing import Any


class ConversationHistory:
    """In-memory conversation history with max turns cap."""

    def __init__(self, max_turns: int = 20):
        """
        Args:
            max_turns: Maximum number of conversation turns to retain.
                      Each turn is a user+assistant pair.
        """
        self.max_turns = max_turns
        self.messages: list[dict[str, str]] = []

    def add(self, role: str, content: str) -> None:
        """
        Add a message to the conversation history.

        Args:
            role: "user" or "assistant"
            content: The message content
        """
        if role not in ("user", "assistant"):
            raise ValueError(f"Invalid role: {role}")
        self.messages.append({"role": role, "content": content})

        # Truncate oldest half when limit exceeded
        max_messages = self.max_turns * 2
        if len(self.messages) > max_messages:
            self.messages = self.messages[-max_messages:]

    def get_messages(self) -> list[dict[str, str]]:
        """Return all messages."""
        return list(self.messages)

    def clear(self) -> None:
        """Clear all messages."""
        self.messages.clear()

    def build_llm_messages(self, system_prompt: str) -> list[dict[str, str]]:
        """
        Build message list for LLM with system prompt at front.

        Args:
            system_prompt: The system prompt to prepend

        Returns:
            List of messages starting with system prompt
        """
        return [{"role": "system", "content": system_prompt}] + self.messages
