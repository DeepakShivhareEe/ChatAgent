"""Bounded, expiring in-memory conversation store.

The browser keeps only an opaque UUID. It never supplies prior messages back to
the model, preventing transcript and role-injection attacks.
"""

from collections import OrderedDict
from dataclasses import dataclass, field
import time


@dataclass
class Conversation:
    messages: list[dict[str, str]] = field(default_factory=list)
    updated_at: float = field(default_factory=time.monotonic)


class ConversationStore:
    def __init__(self, window: int, ttl_seconds: int, max_conversations: int):
        self.window = window
        self.ttl_seconds = ttl_seconds
        self.max_conversations = max_conversations
        self._conversations: OrderedDict[str, Conversation] = OrderedDict()

    def _purge_expired(self, now: float) -> None:
        expired = [
            conversation_id
            for conversation_id, conversation in self._conversations.items()
            if now - conversation.updated_at > self.ttl_seconds
        ]
        for conversation_id in expired:
            del self._conversations[conversation_id]

    def history(self, conversation_id: str) -> list[dict[str, str]]:
        now = time.monotonic()
        self._purge_expired(now)
        conversation = self._conversations.get(conversation_id)
        if not conversation:
            return []
        conversation.updated_at = now
        self._conversations.move_to_end(conversation_id)
        return [message.copy() for message in conversation.messages]

    def append(self, conversation_id: str, role: str, content: str) -> None:
        if role not in {"user", "assistant"}:
            raise ValueError("Only user and assistant messages may be stored.")

        now = time.monotonic()
        self._purge_expired(now)
        conversation = self._conversations.setdefault(conversation_id, Conversation())
        conversation.messages.append({"role": role, "content": content})
        conversation.messages = conversation.messages[-self.window:]
        conversation.updated_at = now
        self._conversations.move_to_end(conversation_id)
        while len(self._conversations) > self.max_conversations:
            self._conversations.popitem(last=False)
