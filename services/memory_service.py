from __future__ import annotations

import uuid
from collections import defaultdict


try:
    from langchain.memory import ConversationBufferMemory
except Exception:  # pragma: no cover - optional dependency
    ConversationBufferMemory = None


class SessionMemoryService:
    def __init__(self) -> None:
        self._history = defaultdict(list)
        self._metadata = defaultdict(dict)
        self._langchain_memories = {}

    def ensure_session_id(self, session_obj) -> str:
        if "chat_session_id" not in session_obj:
            session_obj["chat_session_id"] = str(uuid.uuid4())
        return session_obj["chat_session_id"]

    def _get_langchain_memory(self, session_id: str):
        if ConversationBufferMemory is None:
            return None
        if session_id not in self._langchain_memories:
            self._langchain_memories[session_id] = ConversationBufferMemory(
                return_messages=False,
                input_key="input",
                output_key="output",
            )
        return self._langchain_memories[session_id]

    def add_turn(self, session_id: str, role: str, content: str) -> None:
        if not content:
            return
        self._history[session_id].append({"role": role, "content": content})
        self._history[session_id] = self._history[session_id][-10:]

    def save_exchange(self, session_id: str, user_message: str, assistant_message: str) -> None:
        self.add_turn(session_id, "user", user_message)
        self.add_turn(session_id, "assistant", assistant_message)
        memory = self._get_langchain_memory(session_id)
        if memory is not None:
            memory.save_context({"input": user_message}, {"output": assistant_message})

    def get_history(self, session_id: str) -> list[dict]:
        return list(self._history.get(session_id, []))

    def clear(self, session_id: str) -> None:
        self._history.pop(session_id, None)
        self._metadata.pop(session_id, None)
        self._langchain_memories.pop(session_id, None)

    def set_metadata(self, session_id: str, key: str, value) -> None:
        self._metadata[session_id][key] = value

    def get_metadata(self, session_id: str, key: str, default=None):
        return self._metadata.get(session_id, {}).get(key, default)


memory_service = SessionMemoryService()
