"""
Daneel agent: hybrid LLM chat + fixed evidence reactions.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from spoon_ai.chat import ChatBot, Memory
from spoon_ai.schema import Message


class DaneelAgent:
    """丹尼尔：LLM 自由对话 + 证物触发预设"""

    def __init__(self, content_root: Path) -> None:
        self._content_root = content_root
        self._prompt_path = content_root / "prompts" / "daneel.md"
        self._triggers_path = content_root / "triggers" / "evidence_triggers.json"

        self.llm = ChatBot(
            llm_provider=os.getenv("LLM_PROVIDER", "openai"),
            model_name=os.getenv("OPENAI_COMPATIBLE_MODEL", "claude-sonnet-4-5-20250929"),
            api_key=os.getenv("OPENAI_COMPATIBLE_API_KEY") or os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_COMPATIBLE_BASE_URL") or os.getenv("OPENAI_BASE_URL"),
        )
        self._session_memories: dict[str, Memory] = {}
        self.system_prompt = self._load_prompt()

    def _load_prompt(self) -> str:
        if self._prompt_path.exists():
            return self._prompt_path.read_text(encoding="utf-8")
        return ""

    def _load_triggers(self) -> dict:
        if not self._triggers_path.exists():
            return {}
        return json.loads(self._triggers_path.read_text(encoding="utf-8"))

    def _get_memory(self, session_id: str) -> Memory:
        if session_id not in self._session_memories:
            self._session_memories[session_id] = Memory()
        return self._session_memories[session_id]

    def reset(self) -> None:
        self._session_memories = {}

    async def chat(self, message: str, session_id: str) -> str:
        """LLM 自由对话"""
        memory = self._get_memory(session_id)
        memory.add_message(Message(role="user", content=message))
        reply = await self.llm.ask(messages=memory.messages, system_msg=self.system_prompt)
        reply_text = getattr(reply, "content", None)
        if reply_text is None:
            reply_text = str(reply)
        memory.add_message(Message(role="assistant", content=reply_text))
        return str(reply_text)

    def present_evidence(self, evidence_id: str) -> tuple[str, list[str]]:
        """证物触发：返回固定文本 + 解锁列表"""
        triggers = self._load_triggers().get("daneel", {})
        payload = triggers.get(evidence_id)
        if not payload:
            return "我不太理解你想让我看什么。", []
        return payload.get("response", ""), list(payload.get("unlocks", []))
