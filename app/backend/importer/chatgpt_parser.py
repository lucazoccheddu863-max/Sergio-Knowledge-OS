import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from .base_parser import BaseParser, ParsedConversation, ParsedMessage


class ChatGPTParser(BaseParser):
    @property
    def platform_name(self) -> str:
        return "chatgpt"

    @property
    def supported_extensions(self) -> List[str]:
        return [".json", ".html"]

    def detect_platform(self, file_path: Path) -> bool:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")[:8192]

            if file_path.suffix.lower() == ".json":
                chatgpt_indicators = [
                    '"mapping"',
                    '"conversation_id"',
                    '"moderation_results"',
                ]

                if '"mapping"' in content:
                    return True

                matches = sum(1 for ind in chatgpt_indicators if ind in content)
                if matches >= 2:
                    return True

                return False

            if file_path.suffix.lower() == ".html":
                lower_content = content.lower()
                html_indicators = [
                    "chatgpt",
                    "openai",
                    "conversation",
                    "data-testid",
                ]
                return any(ind in lower_content for ind in html_indicators)

            return False
        except Exception:
            return False

    def can_parse(self, file_path: Path) -> bool:
        return self.detect_platform(file_path)

    def parse_file(self, file_path: Path) -> List[ParsedConversation]:
        suffix = file_path.suffix.lower()
        if suffix == ".json":
            return self._parse_json(file_path)
        elif suffix == ".html":
            return self._parse_html(file_path)
        else:
            raise ValueError(f"Unsupported extension: {suffix}")

    def _parse_json(self, file_path: Path) -> List[ParsedConversation]:
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

        conversation_id = data.get("conversation_id") or data.get("id")

        created_at = None
        if "create_time" in data and data["create_time"]:
            try:
                ts = data["create_time"]
                if isinstance(ts, (int, float)):
                    created_at = datetime.fromtimestamp(ts)
            except (ValueError, OSError, TypeError):
                pass

        updated_at = None
        if "update_time" in data and data["update_time"]:
            try:
                ts = data["update_time"]
                if isinstance(ts, (int, float)):
                    updated_at = datetime.fromtimestamp(ts)
            except (ValueError, OSError, TypeError):
                pass

        messages = []
        mapping = data.get("mapping", {})

        if isinstance(mapping, dict):
            for node_id, node in mapping.items():
                if not isinstance(node, dict):
                    continue
                message_data = node.get("message")
                if not isinstance(message_data, dict):
                    continue

                role = message_data.get("author", {}).get("role", "unknown")
                content_parts = message_data.get("content", {})

                text = ""
                if isinstance(content_parts, dict):
                    parts = content_parts.get("parts", [])
                    if isinstance(parts, list):
                        text = "\n".join(str(p) for p in parts if p is not None)
                    else:
                        text = str(parts)
                else:
                    text = str(content_parts)

                msg_timestamp = None
                if "create_time" in message_data and message_data["create_time"]:
                    try:
                        ts = message_data["create_time"]
                        if isinstance(ts, (int, float)):
                            msg_timestamp = datetime.fromtimestamp(ts)
                    except (ValueError, OSError, TypeError):
                        pass

                if text.strip() or role in ("user", "assistant", "system"):
                    messages.append(ParsedMessage(
                        role=role,
                        content=text,
                        timestamp=msg_timestamp,
                        metadata={"node_id": node_id}
                    ))

        messages.sort(key=lambda m: m.timestamp or datetime.min)

        model = "unknown"
        if "model" in data:
            model = str(data["model"])
        elif "model_slug" in data:
            model = str(data["model_slug"])

        return ParsedConversation(
            title=title,
            messages=messages,
            platform="chatgpt",
            conversation_id=conversation_id,
            created_at=created_at,
            updated_at=updated_at,
            metadata={"model": model}
        )

    def _parse_html(self, file_path: Path) -> List[ParsedConversation]:
        content = file_path.read_text(encoding="utf-8", errors="ignore")

        title_match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else "Untitled"

        messages = []
        text_blocks = re.findall(r'<div[^>]*>([^<]+)</div>', content)
        text_blocks = [t.strip() for t in text_blocks if t.strip()]

        for i, text in enumerate(text_blocks[:50]):
            role = "user" if i % 2 == 0 else "assistant"
            messages.append(ParsedMessage(role=role, content=text))

        if not messages:
            text = re.sub(r"<[^>]+>", "", content)
            text = re.sub(r"\s+", " ", text).strip()
            if text:
                messages.append(ParsedMessage(role="assistant", content=text))

        return [ParsedConversation(
            title=title,
            messages=messages,
            platform="chatgpt",
            metadata={"source": "html"}
        )]
