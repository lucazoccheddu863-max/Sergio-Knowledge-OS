import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from .base_parser import BaseParser, ParsedConversation, ParsedMessage


class GeminiParser(BaseParser):
    @property
    def platform_name(self) -> str:
        return "gemini"

    @property
    def supported_extensions(self) -> List[str]:
        return [".json"]

    def detect_platform(self, file_path: Path) -> bool:
        try:
            if file_path.suffix.lower() != ".json":
                return False

            content = file_path.read_text(encoding="utf-8", errors="ignore")[:8192]

            gemini_indicators = [
                '"candidates"',
                '"content"',
                '"parts"',
                '"role"',
                '"modelVersion"',
            ]

            if '"mapping"' in content:
                return False

            matches = sum(1 for ind in gemini_indicators if ind in content)
            return matches >= 2
        except Exception:
            return False

    def can_parse(self, file_path: Path) -> bool:
        return self.detect_platform(file_path)

    def parse_file(self, file_path: Path) -> List[ParsedConversation]:
        suffix = file_path.suffix.lower()
        if suffix not in self.supported_extensions:
            raise ValueError(f"Unsupported extension: {suffix}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        conversations = []

        if isinstance(data, list):
            items = data
        else:
            items = [data]

        for item in items:
            conv = self._parse_conversation(item)
            if conv:
                conversations.append(conv)

        return conversations

    def _parse_conversation(self, data: Dict[str, Any]) -> Optional[ParsedConversation]:
        title = data.get("title", "Untitled")
        if not title or title.strip() == "":
            title = "Untitled"

        conversation_id = data.get("conversationId") or data.get("id")

        created_at = None
        updated_at = None

        if "createTime" in data and data["createTime"]:
            created_at = self._parse_timestamp(data["createTime"])
        if "updateTime" in data and data["updateTime"]:
            updated_at = self._parse_timestamp(data["updateTime"])

        messages = []

        content = data.get("content", [])
        if isinstance(content, list):
            for entry in content:
                msg = self._parse_message_entry(entry)
                if msg:
                    messages.append(msg)

        if not messages:
            candidates = data.get("candidates", [])
            if isinstance(candidates, list):
                for cand in candidates:
                    content_obj = cand.get("content", {})
                    if isinstance(content_obj, dict):
                        msg = self._parse_message_entry(content_obj)
                        if msg:
                            messages.append(msg)

        model = data.get("modelVersion", "unknown")
        if model == "unknown":
            model = data.get("model", "unknown")

        return ParsedConversation(
            title=title,
            messages=messages,
            platform="gemini",
            conversation_id=conversation_id,
            created_at=created_at,
            updated_at=updated_at,
            metadata={"model": model}
        )

    def _parse_message_entry(self, entry: Dict[str, Any]) -> Optional[ParsedMessage]:
        if not isinstance(entry, dict):
            return None

        role = entry.get("role", "unknown")
        role_map = {
            "user": "user",
            "model": "assistant",
            "system": "system",
        }
        role = role_map.get(role, role)

        text = ""
        parts = entry.get("parts", [])
        if isinstance(parts, list):
            for part in parts:
                if isinstance(part, dict) and "text" in part:
                    text += part["text"]
                elif isinstance(part, str):
                    text += part

        timestamp = None
        if "createTime" in entry:
            timestamp = self._parse_timestamp(entry["createTime"])

        if text.strip() or role in ("user", "assistant", "system"):
            return ParsedMessage(
                role=role,
                content=text,
                timestamp=timestamp,
                metadata={}
            )
        return None

    def _parse_timestamp(self, ts: Any) -> Optional[datetime]:
        if ts is None:
            return None

        try:
            if isinstance(ts, (int, float)):
                if ts > 1e12:
                    return datetime.fromtimestamp(ts / 1000.0)
                else:
                    return datetime.fromtimestamp(ts)
            elif isinstance(ts, str):
                return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except (ValueError, OSError, TypeError):
            pass

        return None
