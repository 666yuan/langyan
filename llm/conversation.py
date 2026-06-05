import os
from typing import AsyncGenerator

import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 300    # 面试回复控制在 2-3 句，不需要太长
MAX_HISTORY = 10    # 保留最近 10 条消息（5 轮对话）


class ConversationManager:
    """
    多轮对话管理器。
    维护对话历史，流式调用 Claude API，将 token 逐个 yield 给调用方。
    """

    def __init__(self):
        self._client = anthropic.AsyncAnthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        self._history: list[dict] = []

    # ── 历史管理 ──────────────────────────────────────────

    def _append(self, role: str, content: str) -> None:
        self._history.append({"role": role, "content": content})
        # 超出上限时丢弃最旧的一对消息（保持 user/assistant 交替）
        if len(self._history) > MAX_HISTORY:
            self._history = self._history[-MAX_HISTORY:]

    def clear(self) -> None:
        """新会话开始时清空历史。"""
        self._history.clear()

    @property
    def history(self) -> list[dict]:
        return list(self._history)

    # ── 核心对话 ──────────────────────────────────────────

    async def chat(
        self,
        user_text: str,
        system_prompt: str,
    ) -> AsyncGenerator[str, None]:
        """
        将用户发言加入历史，流式调用 Claude，逐 token yield 给调用方。
        调用方负责将完整回复加入历史（通过 record_assistant_turn）。

        Usage:
            full = ""
            async for token in manager.chat(user_text, system_prompt):
                full += token
                # 实时发给前端
            manager.record_assistant_turn(full)
        """
        self._append("user", user_text)

        async with self._client.messages.stream(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            messages=self._history,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    def record_assistant_turn(self, full_response: str) -> None:
        """
        流式输出完成后，将完整 AI 回复写入历史。
        与 chat() 分开是为了让调用方在流式传输完成后再调用，避免历史不完整。
        """
        self._append("assistant", full_response)

    async def one_shot(self, prompt: str, system_prompt: str) -> str:
        """
        非流式单次调用，用于纠错/评分等不需要实时输出的场景。
        """
        response = await self._client.messages.create(
            model=MODEL,
            max_tokens=512,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
