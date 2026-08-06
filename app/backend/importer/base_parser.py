from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


@dataclass
class ParsedMessage:
    role: str
    content: str
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedConversation:
    title: str
    messages: List[ParsedMessage]
    platform: str
    conversation_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def message_count(self) -> int:
        return len(self.messages)

    @property
    def full_text(self) -> str:
        lines = []
        for msg in self.messages:
            role_label = msg.role.upper()
            lines.append(f"[{role_label}]: {msg.content}")
        return "\n\n".join(lines)


class BaseParser(ABC):
    @property
    @abstractmethod
    def platform_name(self) -> str:
        pass

    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        pass

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        pass

    @abstractmethod
    def parse_file(self, file_path: Path) -> List[ParsedConversation]:
        pass

    def detect_platform(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.supported_extensions
