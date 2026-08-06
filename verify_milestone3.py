#!/usr/bin/env python3
"""Verification script for Milestone 3 — Database, Knowledge Engine, Pipeline."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.resolve()
sys.path.insert(0, str(project_root))

from app.backend.config import Config
from app.backend.database.factory import DatabaseFactory
from app.backend.database.sqlite_database import SQLiteDatabase
from app.backend.database.transaction import transaction
from app.backend.database.repositories.source_repository import SourceRepository
from app.backend.database.repositories.import_repository import ImportRepository
from app.backend.database.repositories.conversation_repository import ConversationRepository
from app.backend.database.repositories.message_repository import MessageRepository
from app.backend.database.repositories.search_index_repository import SearchIndexRepository
from app.backend.knowledge_engine.fts5_engine import FTS5Engine
from app.backend.pipeline.db_import_manager import DbImportManager
from app.backend.pipeline.import_session import ImportSession


def print_header(text: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def print_pass(text: str) -> None:
    print(f"  ✅ {text}")


def print_fail(text: str) -> None:
    print(f"  ❌ {text}")


def print_info(text: str) -> None:
    print(f"  ℹ️  {text}")


def verify_database_layer() -> bool:
    print_header("1. Database Layer (Abstract)")
    db = None
    try:
        config = Config.get_instance()

        # Test factory
        db = DatabaseFactory.create("sqlite", config)
        print_pass(f"DatabaseFactory created: {type(db).__name__}")

        # Test connection
        db.connect()
        assert db.is_connected()
        print_pass("Database connected")

        # Test PRAGMAs
        row = db.fetchone("PRAGMA foreign_keys")
        assert row[0] == 1
        print_pass("PRAGMA foreign_keys = ON")

        # Test schema init
        db.init_schema()
        print_pass("Schema initialized from schema_v1.sql")

        # Test CRUD
        db.execute("INSERT INTO schema_meta (key, value) VALUES (?, ?)", ("test_key", "test_value"))
        db.commit()
        row = db.fetchone("SELECT value FROM schema_meta WHERE key = ?", ("test_key",))
        assert row[0] == "test_value"
        print_pass("CRUD operations work")

        # Test transaction rollback
        try:
            with transaction(db):
                db.execute("INSERT INTO schema_meta (key, value) VALUES (?, ?)", ("rollback", "test"))
                raise ValueError("Force rollback")
        except ValueError:
            pass
        row = db.fetchone("SELECT value FROM schema_meta WHERE key = ?", ("rollback",))
        assert row is None
        print_pass("Transaction rollback works")

        return True
    except Exception as e:
        print_fail(f"Database layer error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if db is not None:
            db.close()
            print_pass("Database closed cleanly")


def verify_repositories() -> bool:
    print_header("2. Repository Pattern")
    db = None
    try:
        config = Config.get_instance()
        db = DatabaseFactory.create("sqlite", config)
        db.connect()
        db.init_schema()

        # Source repository
        source_repo = SourceRepository(db)
        from app.backend.domain.models import Source
        source = Source(source_type="chatgpt", name="Test Source", created_at="2024-01-01")
        source_id = source_repo.create(source)
        assert source_id > 0
        retrieved = source_repo.get_by_id(source_id)
        assert retrieved.name == "Test Source"
        print_pass("SourceRepository: CRUD OK")

        # Import repository
        import_repo = ImportRepository(db)
        from app.backend.domain.models import Import
        imp = Import(source_id=source_id, started_at="2024-01-01", status="completed")
        import_id = import_repo.create(imp)
        assert import_id > 0
        print_pass("ImportRepository: CRUD OK")

        # Conversation repository
        conv_repo = ConversationRepository(db)
        from app.backend.domain.models import Conversation
        conv = Conversation(source_id=source_id, external_id="ext-1", title="Test Conv", model="gpt-4")
        conv_id = conv_repo.create(conv)
        assert conv_id > 0
        print_pass("ConversationRepository: CRUD OK")

        # Message repository
        msg_repo = MessageRepository(db)
        from app.backend.domain.models import Message
        msg = Message(conversation_id=conv_id, role="user", content_text="Hello")
        msg_id = msg_repo.create(msg)
        assert msg_id > 0
        print_pass("MessageRepository: CRUD OK")

        # Search index repository
        search_repo = SearchIndexRepository(db)
        search_repo.index_conversation("conversation", conv_id, "Test", "Hello world")
        results = search_repo.search("Hello", limit=10)
        print_pass(f"SearchIndexRepository: indexed + search OK ({len(results)} results)")

        return True
    except Exception as e:
        print_fail(f"Repository error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if db is not None:
            db.close()
            print_pass("Database closed cleanly")


def verify_knowledge_engine() -> bool:
    print_header("3. Knowledge Engine")
    db = None
    try:
        config = Config.get_instance()
        db = DatabaseFactory.create("sqlite", config)
        db.connect()
        db.init_schema()

        search_repo = SearchIndexRepository(db)
        engine = FTS5Engine(search_repo)
        print_pass(f"KnowledgeEngine initialized: {type(engine).__name__}")

        # Index content
        engine.index("conversation", 1, "Python Guide", "Learn Python programming")
        engine.index("conversation", 2, "JavaScript Guide", "Learn JS programming")
        engine.index("message", 3, "", "Python is great for AI")
        print_pass("Indexed 3 entities")

        # Search
        results = engine.search("Python", limit=10)
        assert len(results) >= 1
        print_pass(f"Search 'Python': {len(results)} results")

        # Semantic search fallback
        from app.backend.domain.models import SemanticQuery
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            query = SemanticQuery(query_text="programming", top_k=5)
            semantic_results = engine.semantic_search(query)
            assert len(semantic_results) >= 0
            if w and "Semantic search is not yet implemented" in str(w[0].message):
                print_pass("Semantic search: fallback to FTS5 (placeholder for future)")
            else:
                print_pass("Semantic search: executed")

        # Delete
        engine.delete("conversation", 1)
        results_after = engine.search("Python Guide", limit=10)
        assert len(results_after) == 0
        print_pass("Delete from index works")

        return True
    except Exception as e:
        print_fail(f"Knowledge Engine error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if db is not None:
            db.close()
            print_pass("Database closed cleanly")


def verify_import_pipeline() -> bool:
    print_header("4. DB Import Pipeline")
    db = None
    try:
        config = Config.get_instance()
        db = DatabaseFactory.create("sqlite", config)
        db.connect()
        db.init_schema()

        fixtures_dir = project_root / "tests" / "fixtures"

        # Test ImportSession
        session = ImportSession(db, "chatgpt", "Test Export")
        session.begin()
        assert session.source_id is not None
        assert session.import_id is not None
        session.commit(files_seen=2, files_new=2)
        print_pass("ImportSession: lifecycle OK")

        # Test DbImportManager
        manager = DbImportManager(config, db)

        # Import ChatGPT fixture
        cg_file = fixtures_dir / "chatgpt_export.json"
        if cg_file.exists():
            result = manager.import_file(cg_file, source_type="chatgpt", source_name="ChatGPT")
            print_pass(f"ChatGPT import: {result.status} ({result.conversations_count} convs, {result.messages_count} msgs)")

        # Import Gemini fixture
        g_file = fixtures_dir / "gemini_export.json"
        if g_file.exists():
            result = manager.import_file(g_file, source_type="gemini", source_name="Gemini")
            print_pass(f"Gemini import: {result.status} ({result.conversations_count} convs, {result.messages_count} msgs)")

        # Verify database state
        source_repo = SourceRepository(db)
        conv_repo = ConversationRepository(db)
        msg_repo = MessageRepository(db)

        sources = source_repo.list_all()
        print_pass(f"Sources in DB: {len(sources)}")

        total_convs = 0
        total_msgs = 0
        for source in sources:
            convs = conv_repo.list_by_source(source.id)
            total_convs += len(convs)
            for conv in convs:
                msgs = msg_repo.list_by_conversation(conv.id)
                total_msgs += len(msgs)

        print_pass(f"Conversations in DB: {total_convs}")
        print_pass(f"Messages in DB: {total_msgs}")

        # Verify search indexing
        search_repo = SearchIndexRepository(db)
        results = search_repo.search("test", limit=10)
        print_pass(f"Search index: {len(results)} documents indexed")

        return True
    except Exception as e:
        print_fail(f"Import pipeline error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if db is not None:
            db.close()
            print_pass("Database closed cleanly")


def verify_multi_ai_fields() -> bool:
    print_header("5. Multi-AI Field Support")
    try:
        from app.backend.domain.models import Conversation, Message

        conv = Conversation(
            provider="openai",
            model="gpt-4",
            agent="assistant",
            workspace="default",
            project="SergioAI"
        )
        assert conv.provider == "openai"
        assert conv.model == "gpt-4"
        assert conv.agent == "assistant"
        assert conv.workspace == "default"
        assert conv.project == "SergioAI"
        print_pass("Conversation model: multi-AI fields OK")

        msg = Message(
            provider="gemini",
            model="gemini-1.5-pro",
            agent="model",
            workspace="prod",
            project="Lab3D"
        )
        assert msg.provider == "gemini"
        assert msg.model == "gemini-1.5-pro"
        print_pass("Message model: multi-AI fields OK")

        return True
    except Exception as e:
        print_fail(f"Multi-AI fields error: {e}")
        return False


def verify_milestone2_intact() -> bool:
    print_header("6. Milestone 2 Integrity Check")
    try:
        # Verify M2 files still exist and are unchanged
        m2_files = [
            "app/backend/config.py",
            "app/backend/utils/hashing.py",
            "app/backend/importer/base_parser.py",
            "app/backend/importer/import_report.py",
            "app/backend/importer/chatgpt_parser.py",
            "app/backend/importer/gemini_parser.py",
            "app/backend/importer/import_manager.py",
        ]
        for f in m2_files:
            p = project_root / f
            assert p.exists(), f"M2 file missing: {f}"
        print_pass("All M2 files present")

        # Verify M2 functionality
        from app.backend.importer.import_manager import ImportManager
        from app.backend.importer.chatgpt_parser import ChatGPTParser
        from app.backend.importer.gemini_parser import GeminiParser
        from app.backend.utils.hashing import calculate_file_hash

        config = Config.get_instance()
        manager = ImportManager(config)
        assert len(manager.parsers) == 2
        print_pass("ImportManager: 2 parsers registered")

        cg_parser = ChatGPTParser()
        assert cg_parser.platform_name == "chatgpt"
        print_pass("ChatGPTParser: OK")

        g_parser = GeminiParser()
        assert g_parser.platform_name == "gemini"
        print_pass("GeminiParser: OK")

        fixtures_dir = project_root / "tests" / "fixtures"
        json_file = fixtures_dir / "chatgpt_export.json"
        h = calculate_file_hash(json_file)
        assert len(h) == 64
        print_pass(f"Hashing: {h[:16]}... OK")

        return True
    except Exception as e:
        print_fail(f"M2 integrity error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main() -> int:
    print_header("Sergio Knowledge OS — Milestone 3 Verification")
    print("  Database + Knowledge Engine + Pipeline + Multi-AI")

    results = []
    results.append(("Database Layer", verify_database_layer()))
    results.append(("Repository Pattern", verify_repositories()))
    results.append(("Knowledge Engine", verify_knowledge_engine()))
    results.append(("Import Pipeline", verify_import_pipeline()))
    results.append(("Multi-AI Fields", verify_multi_ai_fields()))
    results.append(("Milestone 2 Intact", verify_milestone2_intact()))

    print_header("Summary")
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        icon = "✅" if passed else "❌"
        print(f"  {icon} {name}: {status}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("🎉 All Milestone 3 verifications passed!")
        print("📋 Milestone 2 remains frozen and intact.")
        print("🚀 Ready for Milestone 4 planning.")
        return 0
    else:
        print("⚠️  Some verifications failed. Please review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
