from __future__ import annotations
from typing import Any
from langchain_core.messages import AIMessage, ToolMessage

def final_ai_text_from_messages(messages: list[Any]) -> str:
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            return msg.content if isinstance(msg.content, str) else str(msg.content)
    return ''

def _tool_call_field(tc: Any, key: str) -> Any:
    if isinstance(tc, dict):
        return tc.get(key)
    return getattr(tc, key, None)

def tool_calls_log_from_messages(messages: list[Any]) -> list[dict[str, str]]:
    log: list[dict[str, str]] = []
    for i, msg in enumerate(messages):
        if not isinstance(msg, AIMessage) or not msg.tool_calls:
            continue
        for tc in msg.tool_calls:
            name = _tool_call_field(tc, 'name') or ''
            args = _tool_call_field(tc, 'args')
            tid = _tool_call_field(tc, 'id')
            obs = ''
            for j in range(i + 1, len(messages)):
                tm = messages[j]
                if isinstance(tm, ToolMessage) and getattr(tm, 'tool_call_id', None) == tid:
                    obs = tm.content
                    break
            s = str(obs)
            log.append({'tool': str(name), 'input': str(args), 'output_summary': s[:200] + '...' if len(s) > 200 else s})
    return log
