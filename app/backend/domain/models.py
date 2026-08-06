from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List


@dataclass
class Source:
    id: Optional[int] = None
    source_type: str = ""
    name: str = ""
    root_path: Optional[str] = None
    created_at: Optional[str] = None
    last_import_at: Optional[str] = None
    is_original_immutable: bool = True
    notes: Optional[str] = None


@dataclass
class Import:
    id: Optional[int] = None
    source_id: int = 0
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    status: str = "pending"
    files_seen: int = 0
    files_new: int = 0
    files_duplicate: int = 0
    errors_count: int = 0
    report_path: Optional[str] = None


@dataclass
class Conversation:
    id: Optional[int] = None
    source_id: Optional[int] = None
    external_id: Optional[str] = None
    title: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    agent: Optional[str] = None
    workspace: Optional[str] = None
    project: Optional[str] = None
    url: Optional[str] = None
    raw_json_path: Optional[str] = None


@dataclass
class Message:
    id: Optional[int] = None
    conversation_id: int = 0
    parent_message_id: Optional[int] = None
    role: Optional[str] = None
    author: Optional[str] = None
    content_text: Optional[str] = None
    created_at: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    agent: Optional[str] = None
    workspace: Optional[str] = None
    project: Optional[str] = None
    metadata_json: Optional[str] = None


@dataclass
class SearchResult:
    entity_type: str
    entity_id: int
    title: Optional[str] = None
    body: Optional[str] = None
    rank: Optional[float] = None


@dataclass
class SemanticQuery:
    query_text: str
    embedding: Optional[List[float]] = None
    top_k: int = 10
