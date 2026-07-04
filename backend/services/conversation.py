"""
services/conversation.py

Redis-backed conversation history store with sliding window and optional
LLM-based summarisation.

Features:
  - Sliding window of ``max_history_turns`` turns (each turn = 2 messages:
    user + assistant).
  - Token-count budget enforced at ``max_history_tokens``.
  - Summarisation triggered at ``summarization_trigger_turns`` when
    ``summarization_enabled`` is True.
  - Session TTL managed via Redis EXPIRE at ``session_ttl_seconds``.
  - ``redis`` is lazily imported; falls back to in-process dict when Redis
    is unavailable.
"""

from __future__ import annotations

import json
import logging
from typing import Dict, List, Optional

from app.config import ConversationSettings, RedisSettings, get_settings
from app.models import ChatMessage, MessageRole

logger = logging.getLogger(__name__)

# Approximate chars-per-token ratio for budget estimation
_CHARS_PER_TOKEN = 4


class ConversationStore:
    """
    Manages per-session conversation history.

    Parameters
    ----------
    conversation_settings:
        Override ``ConversationSettings`` (mainly for testing).
    redis_settings:
        Override ``RedisSettings`` (mainly for testing).
    """

    def __init__(
        self,
        conversation_settings: Optional[ConversationSettings] = None,
        redis_settings: Optional[RedisSettings] = None,
    ) -> None:
        cfg = get_settings()
        self._conv_cfg: ConversationSettings = conversation_settings or cfg.conversation
        self._redis_cfg: RedisSettings = redis_settings or cfg.redis
        self._redis_client = None  # Lazy init
        # In-process fallback when Redis is unavailable
        self._fallback: Dict[str, List[str]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_message(self, session_id: str, message: ChatMessage, user_id: str) -> None:
        """Append *message* to the session history, then trim if needed."""
        key = self._key(session_id, user_id)
        serialised = message.model_dump_json(by_alias=True)
        client = self._get_client()

        if client is not None:
            try:
                client.rpush(key, serialised)
                ttl = self._conv_cfg.session_ttl_seconds
                if ttl > 0:
                    client.expire(key, ttl)
                self._trim_redis(client, key)
                return
            except Exception as exc:  # noqa: BLE001
                logger.warning("ConversationStore.add_message (Redis) failed: %s", exc)

        # Fallback
        history = self._fallback.setdefault(key, [])
        history.append(serialised)
        self._trim_fallback(key)

    def get_history(self, session_id: str, user_id: str) -> List[ChatMessage]:
        """Return the conversation history for *session_id*."""
        key = self._key(session_id, user_id)
        client = self._get_client()

        raw_list: List[str] = []
        if client is not None:
            try:
                raw_list = client.lrange(key, 0, -1)
            except Exception as exc:  # noqa: BLE001
                logger.warning("ConversationStore.get_history (Redis) failed: %s", exc)
                raw_list = self._fallback.get(key, [])
        else:
            raw_list = self._fallback.get(key, [])

        messages: List[ChatMessage] = []
        for raw in raw_list:
            try:
                messages.append(ChatMessage.model_validate_json(raw))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Could not parse stored message: %s", exc)

        return messages

    def summarize_if_needed(self, session_id: str, user_id: str) -> None:
        """
        Trigger summarisation when the session history exceeds
        ``summarization_trigger_turns`` turns (if summarisation is enabled).

        The summarisation call is best-effort; failures are logged and ignored.
        """
        if not self._conv_cfg.summarization_enabled:
            return

        history = self.get_history(session_id, user_id)
        num_turns = len(history) // 2  # user+assistant pairs

        if num_turns < self._conv_cfg.summarization_trigger_turns:
            return

        logger.info(
            "Session %s has %d turns ≥ trigger %d; summarising.",
            session_id,
            num_turns,
            self._conv_cfg.summarization_trigger_turns,
        )

        try:
            self._summarise(session_id, user_id, history)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Summarisation failed for session %s: %s", session_id, exc)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _summarise(self, session_id: str, user_id: str, history: List[ChatMessage]) -> None:
        """Replace history with a summary + the most recent turns."""
        from prompts.templates import render_summarization_prompt  # noqa: PLC0415

        history_text = "\n".join(
            f"{m.role.value.upper()}: {m.content}" for m in history
        )
        prompt = render_summarization_prompt(history_text)

        # Use the configured LLM to summarise
        summary_text = self._call_llm(prompt)
        if not summary_text:
            return

        summary_message = ChatMessage(
            role=MessageRole.ASSISTANT,
            content=f"[Summary of earlier conversation]\n{summary_text}",
        )

        # Keep only the last 2 turns (4 messages) + the summary
        recent = history[-4:] if len(history) > 4 else []
        new_history: List[ChatMessage] = [summary_message] + recent

        key = self._key(session_id, user_id)
        client = self._get_client()
        serialised_list = [m.model_dump_json(by_alias=True) for m in new_history]

        if client is not None:
            try:
                client.delete(key)
                if serialised_list:
                    client.rpush(key, *serialised_list)
                return
            except Exception as exc:  # noqa: BLE001
                logger.warning("Redis replace for summarisation failed: %s", exc)

        self._fallback[key] = serialised_list

    def _call_llm(self, prompt: str) -> Optional[str]:
        """Minimal LLM call for summarisation — avoids circular imports."""
        try:
            cfg = get_settings()
            provider = cfg.llm.provider.value
            api_key = cfg.resolved_llm_api_key()

            if provider == "anthropic":
                # pyrefly: ignore [missing-import]
                import anthropic  # noqa: PLC0415
                client = anthropic.Anthropic(api_key=api_key)
                msg = client.messages.create(
                    model=cfg.llm.model_name,
                    max_tokens=512,
                    messages=[{"role": "user", "content": prompt}],
                )
                return msg.content[0].text if msg.content else None

            if provider in ("openai", "groq", "openrouter"):
                import openai  # noqa: PLC0415
                oc = openai.OpenAI(api_key=api_key, base_url=cfg.resolved_llm_base_url())
                resp = oc.chat.completions.create(
                    model=cfg.llm.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=512,
                )
                return resp.choices[0].message.content

        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM summarisation call failed: %s", exc)

        return None

    def _trim_redis(self, client: object, key: str) -> None:
        """Keep only the last (max_history_turns * 2) messages."""
        max_msgs = self._conv_cfg.max_history_turns * 2
        client.ltrim(key, -max_msgs, -1)
        # Token budget trim
        self._trim_by_tokens_redis(client, key)

    def _trim_by_tokens_redis(self, client: object, key: str) -> None:
        raw_list = client.lrange(key, 0, -1)
        total_chars = sum(len(r) for r in raw_list)
        while total_chars > self._conv_cfg.max_history_tokens * _CHARS_PER_TOKEN and raw_list:
            removed = raw_list.pop(0)
            total_chars -= len(removed)
            client.lpop(key)

    def _trim_fallback(self, key: str) -> None:
        history = self._fallback.get(key, [])
        max_msgs = self._conv_cfg.max_history_turns * 2
        if len(history) > max_msgs:
            self._fallback[key] = history[-max_msgs:]

    def _get_client(self) -> Optional[object]:
        if self._redis_client is not None:
            return self._redis_client
        try:
            import redis as redis_lib  # noqa: PLC0415
            self._redis_client = redis_lib.Redis.from_url(
                self._redis_cfg.url,
                socket_timeout=self._redis_cfg.socket_timeout,
                socket_connect_timeout=self._redis_cfg.socket_connect_timeout,
                decode_responses=True,
            )
            self._redis_client.ping()
            return self._redis_client
        except ImportError:
            logger.warning(
                "redis not installed — ConversationStore using in-process fallback. "
                "Install with: pip install redis"
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("ConversationStore: Redis unavailable (%s) — using fallback.", exc)
        return None

    @staticmethod
    def _key(session_id: str, user_id: str) -> str:
        return f"{user_id}:conversation:{session_id}"


__all__ = ["ConversationStore"]
