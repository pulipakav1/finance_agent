"""Session memory helpers built around thread IDs."""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.memory import MemorySaver

from src.fin_platform.config import settings


class SessionMemoryManager:
    def __init__(self) -> None:
        self.checkpointer = MemorySaver()

    def trim_history(self, history: list[dict[str, str]]) -> list[dict[str, str]]:
        if len(history) <= settings.max_history_turns:
            return history
        # Keep first context and latest turns to avoid unbounded growth.
        return [history[0], *history[-(settings.max_history_turns - 1) :]]

    def summarize_history(self, history: list[dict[str, str]]) -> str:
        if not history:
            return ""
        recent = self.trim_history(history)[-4:]
        return " | ".join(f"{item['role']}: {item['content'][:120]}" for item in recent)

    def enrich_metadata(self, thread_id: str, session_metadata: dict[str, Any] | None) -> dict[str, Any]:
        payload = dict(session_metadata or {})
        payload["thread_id"] = thread_id
        return payload
