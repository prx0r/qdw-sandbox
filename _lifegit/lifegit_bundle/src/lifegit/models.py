from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class NormalizedMessage:
    provider: str
    conversation_id: str
    message_id: str
    parent_message_id: str | None
    role: str
    text: str
    created_at: str | None
    model: str | None = None
    is_current_path: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class NormalizedConversation:
    provider: str
    conversation_id: str
    title: str
    created_at: str | None
    updated_at: str | None
    messages: tuple[NormalizedMessage, ...]
    metadata: dict[str, Any] = field(default_factory=dict)
