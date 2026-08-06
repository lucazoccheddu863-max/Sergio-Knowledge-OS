"""Database-integrated import manager.

This is an adapter/wrapper around the Milestone 2 ImportManager.
It uses ImportManager for parsing and hashing, then persists results
to the database via repositories.

Design principle: ImportManager (M2) is NOT modified. This adapter
only uses its public interface.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from ..importer.import_manager import ImportManager
from ..importer.import_report import ImportReport, FileImportResult
from ..database.database import Database
from ..database.repositories.source_repository import SourceRepository
from ..database.repositories.import_repository import ImportRepository
from ..database.repositories.conversation_repository import ConversationRepository
from ..database.repositories.message_repository import MessageRepository
from ..database.repositories.search_index_repository import SearchIndexRepository
from ..knowledge_engine.engine import KnowledgeEngine
from ..knowledge_engine.fts5_engine import FTS5Engine
from ..domain.models import Conversation, Message
from .import_session import ImportSession


class DbImportManager:
    """Database-aware import manager.

    Wraps ImportManager (M2) to add database persistence.
    Does NOT modify ImportManager or any M2 files.
    """

    def __init__(self, config, db: Database, knowledge_engine: Optional[KnowledgeEngine] = None) -> None:
        self._config = config
        self._db = db
        self._m2_manager = ImportManager(config)
        self._conv_repo = ConversationRepository(db)
        self._msg_repo = MessageRepository(db)
        self._search_repo = SearchIndexRepository(db)
        self._knowledge = knowledge_engine or FTS5Engine(self._search_repo)

    def import_file(self, file_path: Path, source_type: str = "unknown", source_name: str = "unknown") -> FileImportResult:
        """Import a single file with database persistence.

        Args:
            file_path: Path to the export file
            source_type: Type of source (e.g., "chatgpt", "gemini")
            source_name: Human-readable source name

        Returns:
            FileImportResult from M2 ImportManager
        """
        # Step 1: Use M2 ImportManager for parsing and deduplication
        result = self._m2_manager.import_file(file_path)

        if result.status in ("new", "modified"):
            # Step 2: Create import session
            session = ImportSession(self._db, source_type, source_name, str(file_path.parent))
            session.begin()

            try:
                # Step 3: Re-parse to get conversation data for DB
                parser = self._m2_manager._get_parser(file_path)
                if parser:
                    conversations = parser.parse_file(file_path)
                    self._persist_conversations(conversations, session.source_id, source_type)

                session.commit(files_seen=1, files_new=1 if result.status == "new" else 0)
            except Exception:
                session.rollback()
                raise

        return result

    def import_directory(self, directory: Path, source_type: str = "unknown", source_name: str = "unknown") -> ImportReport:
        """Import all supported files in a directory with database persistence.

        Args:
            directory: Directory containing export files
            source_type: Type of source
            source_name: Human-readable source name

        Returns:
            ImportReport from M2 ImportManager
        """
        # Step 1: Use M2 ImportManager for directory import
        report = self._m2_manager.import_directory(directory)

        # Step 2: Create import session for the batch
        session = ImportSession(self._db, source_type, source_name, str(directory))
        session.begin()

        try:
            # Step 3: Persist all new/modified files
            for file_result in report.file_results:
                if file_result.status in ("new", "modified"):
                    parser = self._m2_manager._get_parser(file_result.file_path)
                    if parser:
                        conversations = parser.parse_file(file_result.file_path)
                        self._persist_conversations(
                            conversations, session.source_id,
                            parser.platform_name
                        )

            session.commit(
                files_seen=report.files_processed,
                files_new=report.files_new,
                files_duplicate=report.files_duplicate,
                errors_count=report.files_error
            )
        except Exception:
            session.rollback()
            raise

        return report

    def _persist_conversations(self, conversations: List, source_id: Optional[int], provider: str) -> None:
        """Persist parsed conversations and messages to the database.

        Args:
            conversations: List of ParsedConversation from M2 parsers
            source_id: Database source ID
            provider: AI provider name (e.g., "chatgpt", "gemini")
        """
        now = datetime.now(timezone.utc).isoformat()

        for parsed_conv in conversations:
            # Check if conversation already exists by external_id
            external_id = parsed_conv.conversation_id or parsed_conv.metadata.get("conversation_id")
            existing = None
            if external_id and source_id:
                existing = self._conv_repo.get_by_external_id(external_id, source_id)

            if existing:
                conv_id = existing.id
            else:
                # Create conversation
                conv = Conversation(
                    source_id=source_id,
                    external_id=external_id,
                    title=parsed_conv.title,
                    created_at=now,
                    updated_at=now,
                    model=parsed_conv.metadata.get("model"),
                    provider=provider,
                )
                conv_id = self._conv_repo.create(conv)

            # Create messages
            messages = []
            for parsed_msg in parsed_conv.messages:
                msg = Message(
                    conversation_id=conv_id,
                    role=parsed_msg.role,
                    content_text=parsed_msg.content,
                    created_at=parsed_msg.timestamp.isoformat() if parsed_msg.timestamp else now,
                    model=parsed_conv.metadata.get("model"),
                    provider=provider,
                    metadata_json=str(parsed_msg.metadata) if parsed_msg.metadata else None,
                )
                messages.append(msg)

            if messages:
                self._msg_repo.create_many(messages)

            # Index for search
            full_text = parsed_conv.full_text
            self._knowledge.index(
                entity_type="conversation",
                entity_id=conv_id,
                title=parsed_conv.title,
                body=full_text,
                source_name=provider,
            )

    def reset_database(self) -> None:
        """Clear all persisted data. Useful for testing."""
        self._db.execute("DELETE FROM messages")
        self._db.execute("DELETE FROM conversations")
        self._db.execute("DELETE FROM imports")
        self._db.execute("DELETE FROM sources")
        self._knowledge.clear()
        self._db.commit()
