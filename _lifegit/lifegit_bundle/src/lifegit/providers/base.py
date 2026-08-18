from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from lifegit.models import NormalizedConversation


class Provider(ABC):
    name: str

    @abstractmethod
    def parse(self, path: Path) -> tuple[list[NormalizedConversation], str, str]:
        """Return conversations, artifact SHA-256, artifact member/name."""
        raise NotImplementedError
