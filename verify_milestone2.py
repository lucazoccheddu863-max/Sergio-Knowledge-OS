#!/usr/bin/env python3
"""Verification script for Milestone 2 — Import Manager."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.resolve()
sys.path.insert(0, str(project_root))

from app.backend.config import Config
from app.backend.importer.chatgpt_parser import ChatGPTParser
from app.backend.importer.gemini_parser import GeminiParser
from app.backend.importer.import_manager import ImportManager
from app.backend.utils.hashing import calculate_file_hash


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


def verify_config() -> bool:
    print_header("1. Configuration")
    try:
        config_path = project_root / "config.yaml"
        if not config_path.exists():
            print_fail("config.yaml not found")
            return False

        config = Config.load(config_path)
        print_pass(f"Config loaded from: {config_path}")
        print_pass(f"Database path: {config.database_path}")
        print_pass(f"Archive root: {config.archive_root}")
        print_pass(f"ChatGPT import dir: {config.chatgpt_import_dir}")
        print_pass(f"Gemini import dir: {config.gemini_import_dir}")
        print_pass(f"Hash algorithm: {config.hash_algorithm}")
        print_pass(f"AI provider: {config.ai_primary_provider}")
        print_pass(f"Local model: {config.ai_local_model}")

        config.ensure_directories()
        print_pass("All directories created/verified")
        return True
    except Exception as e:
        print_fail(f"Config error: {e}")
        return False


def verify_hashing() -> bool:
    print_header("2. File Hashing")
    try:
        fixtures_dir = project_root / "tests" / "fixtures"
        json_file = fixtures_dir / "chatgpt_export.json"

        if not json_file.exists():
            print_fail(f"Fixture not found: {json_file}")
            return False

        hash1 = calculate_file_hash(json_file)
        hash2 = calculate_file_hash(json_file)

        print_pass(f"Hash calculated: {hash1[:16]}...")
        print_pass(f"Hash is consistent: {hash1 == hash2}")
        print_pass(f"Hash length correct: {len(hash1) == 64}")
        return True
    except Exception as e:
        print_fail(f"Hashing error: {e}")
        return False


def verify_chatgpt_parser() -> bool:
    print_header("3. ChatGPT Parser")
    try:
        parser = ChatGPTParser()
        print_pass(f"Parser initialized: {parser.platform_name}")

        fixtures_dir = project_root / "tests" / "fixtures"

        json_file = fixtures_dir / "chatgpt_export.json"
        if json_file.exists():
            if parser.can_parse(json_file):
                print_pass(f"Can parse JSON: {json_file.name}")
                conversations = parser.parse_file(json_file)
                print_pass(f"Parsed {len(conversations)} conversations from JSON")
                for conv in conversations:
                    print_pass(f"  → '{conv.title}' ({conv.message_count} msgs, {conv.metadata.get('model', 'unknown')})")
            else:
                print_fail(f"Cannot parse JSON: {json_file.name}")
                return False

        html_file = fixtures_dir / "chatgpt_export.html"
        if html_file.exists():
            if parser.can_parse(html_file):
                print_pass(f"Can parse HTML: {html_file.name}")
                conversations = parser.parse_file(html_file)
                print_pass(f"Parsed {len(conversations)} conversation(s) from HTML")
            else:
                print_fail(f"Cannot parse HTML: {html_file.name}")
                return False

        return True
    except Exception as e:
        print_fail(f"ChatGPT parser error: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_gemini_parser() -> bool:
    print_header("4. Gemini Parser")
    try:
        parser = GeminiParser()
        print_pass(f"Parser initialized: {parser.platform_name}")

        fixtures_dir = project_root / "tests" / "fixtures"
        json_file = fixtures_dir / "gemini_export.json"

        if json_file.exists():
            if parser.can_parse(json_file):
                print_pass(f"Can parse JSON: {json_file.name}")
                conversations = parser.parse_file(json_file)
                print_pass(f"Parsed {len(conversations)} conversations from JSON")
                for conv in conversations:
                    print_pass(f"  → '{conv.title}' ({conv.message_count} msgs, {conv.metadata.get('model', 'unknown')})")
            else:
                print_fail(f"Cannot parse JSON: {json_file.name}")
                return False
        else:
            print_fail(f"Fixture not found: {json_file}")
            return False

        return True
    except Exception as e:
        print_fail(f"Gemini parser error: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_incremental_import() -> bool:
    print_header("5. Incremental Import")
    try:
        config = Config.get_instance()
        manager = ImportManager(config)

        manager.reset_index()
        print_info("Index reset for clean test")

        fixtures_dir = project_root / "tests" / "fixtures"

        # Test 1: First import — NEW
        json_file = fixtures_dir / "chatgpt_export.json"
        result1 = manager.import_file(json_file)

        if result1.status == "new":
            print_pass(f"First import: NEW ({result1.conversations_count} conversations, {result1.messages_count} messages)")
        else:
            print_fail(f"First import should be NEW, got: {result1.status}")
            return False

        # Test 2: Second import — DUPLICATE
        result2 = manager.import_file(json_file)

        if result2.status == "duplicate":
            print_pass(f"Second import: DUPLICATE (hash unchanged)")
        else:
            print_fail(f"Second import should be DUPLICATE, got: {result2.status}")
            return False

        # Test 3: Modified file — MODIFIED (same file, not a copy)
        original_content = json_file.read_text()
        json_file.write_text(original_content + "\n")

        result3 = manager.import_file(json_file)
        json_file.write_text(original_content)  # Restore immediately

        if result3.status == "modified":
            print_pass(f"Modified file: MODIFIED (hash changed)")
        else:
            print_fail(f"Modified file should be MODIFIED, got: {result3.status}")
            return False

        # Test 4: Directory import with report
        report = manager.import_directory(fixtures_dir)

        print_pass(f"Directory import completed")
        print_pass(f"  Files processed: {report.files_processed}")
        print_pass(f"  New: {report.files_new}")
        print_pass(f"  Modified: {report.files_modified}")
        print_pass(f"  Duplicate: {report.files_duplicate}")
        print_pass(f"  Ignored: {report.files_ignored}")
        print_pass(f"  Error: {report.files_error}")
        print_pass(f"  Conversations: {report.conversations_imported}")
        print_pass(f"  Messages: {report.messages_imported}")
        print_pass(f"  Success rate: {report.success_rate:.1f}%")
        print_pass(f"  Duration: {report.duration_seconds:.3f}s")

        # Test 5: Re-import (all duplicates)
        report2 = manager.import_directory(fixtures_dir)

        if report2.files_new == 0 and report2.files_duplicate > 0:
            print_pass(f"Re-import: all files marked as duplicate (incremental working)")
        else:
            print_fail(f"Re-import should mark all as duplicate")
            return False

        print("\n" + str(report))
        return True
    except Exception as e:
        print_fail(f"Incremental import error: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_parsed_data() -> bool:
    print_header("6. Parsed Data Quality")
    try:
        fixtures_dir = project_root / "tests" / "fixtures"

        cg_parser = ChatGPTParser()
        cg_convs = cg_parser.parse_file(fixtures_dir / "chatgpt_export.json")

        total_messages = sum(c.message_count for c in cg_convs)
        print_pass(f"ChatGPT: {len(cg_convs)} conversations, {total_messages} total messages")

        for conv in cg_convs:
            assert conv.title, "Conversation must have title"
            assert conv.messages, "Conversation must have messages"
            assert conv.platform == "chatgpt"
            for msg in conv.messages:
                assert msg.role in ("user", "assistant", "system")
                assert msg.content.strip(), "Message content must not be empty"
        print_pass("All ChatGPT conversations have valid structure")

        g_parser = GeminiParser()
        g_convs = g_parser.parse_file(fixtures_dir / "gemini_export.json")

        total_messages = sum(c.message_count for c in g_convs)
        print_pass(f"Gemini: {len(g_convs)} conversations, {total_messages} total messages")

        for conv in g_convs:
            assert conv.title, "Conversation must have title"
            assert conv.messages, "Conversation must have messages"
            assert conv.platform == "gemini"
            for msg in conv.messages:
                assert msg.role in ("user", "assistant", "system")
                assert msg.content.strip(), "Message content must not be empty"
        print_pass("All Gemini conversations have valid structure")

        sample = cg_convs[0]
        full = sample.full_text
        assert "[USER]:" in full
        assert "[ASSISTANT]:" in full
        print_pass("Full text generation works correctly")

        return True
    except Exception as e:
        print_fail(f"Data quality error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main() -> int:
    print_header("Sergio Knowledge OS — Milestone 2 Verification")
    print("  Import Manager: Config + Hashing + Parsers + Incremental Import")

    results = []
    results.append(("Configuration", verify_config()))
    results.append(("File Hashing", verify_hashing()))
    results.append(("ChatGPT Parser", verify_chatgpt_parser()))
    results.append(("Gemini Parser", verify_gemini_parser()))
    results.append(("Incremental Import", verify_incremental_import()))
    results.append(("Data Quality", verify_parsed_data()))

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
        print("🎉 All verifications passed!")
        print("📋 Next step: Test with your REAL ChatGPT and Gemini exports.")
        print("   Copy your exports to:")
        config = Config.get_instance()
        print(f"   - ChatGPT: {config.chatgpt_import_dir}")
        print(f"   - Gemini:  {config.gemini_import_dir}")
        print("   Then run: python verify_milestone2.py")
        return 0
    else:
        print("⚠️  Some verifications failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
