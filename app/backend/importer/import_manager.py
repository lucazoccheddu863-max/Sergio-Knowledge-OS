import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..config import Config
from ..utils.hashing import calculate_file_hash
from .base_parser import BaseParser
from .chatgpt_parser import ChatGPTParser
from .gemini_parser import GeminiParser
from .import_report import FileImportResult, ImportReport


class ImportManager:
    def __init__(self, config: Config):
        self.config = config
        self.parsers: List[BaseParser] = [
            ChatGPTParser(),
            GeminiParser(),
        ]
        self._index: Dict[str, Dict] = {}

    def reset_index(self) -> None:
        self._index = {}

    def _get_parser(self, file_path: Path) -> Optional[BaseParser]:
        for parser in self.parsers:
            if parser.can_parse(file_path):
                return parser
        return None

    def _load_index(self) -> None:
        index_path = self.config.database_path.parent / "import_index.json"
        if index_path.exists():
            try:
                with open(index_path, "r", encoding="utf-8") as f:
                    self._index = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._index = {}

    def _save_index(self) -> None:
        index_path = self.config.database_path.parent / "import_index.json"
        index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(self._index, f, indent=2, default=str)

    def import_file(self, file_path: Path) -> FileImportResult:
        if not file_path.exists():
            return FileImportResult(
                file_path=file_path,
                status="error",
                error_message="File not found"
            )

        parser = self._get_parser(file_path)
        if parser is None:
            return FileImportResult(
                file_path=file_path,
                status="ignored",
                error_message="No parser available for this file type"
            )

        try:
            file_hash = calculate_file_hash(file_path, self.config.hash_algorithm)
        except Exception as e:
            return FileImportResult(
                file_path=file_path,
                status="error",
                error_message=f"Hash calculation failed: {e}"
            )

        file_key = str(file_path.resolve())
        existing = self._index.get(file_key)

        if existing is None:
            status = "new"
        elif existing.get("hash") == file_hash:
            return FileImportResult(
                file_path=file_path,
                status="duplicate",
                hash=file_hash,
                conversations_count=existing.get("conversations_count", 0),
                messages_count=existing.get("messages_count", 0),
                platform=existing.get("platform")
            )
        else:
            status = "modified"

        try:
            conversations = parser.parse_file(file_path)
        except Exception as e:
            return FileImportResult(
                file_path=file_path,
                status="error",
                hash=file_hash,
                error_message=f"Parse failed: {e}"
            )

        messages_count = sum(c.message_count for c in conversations)

        self._index[file_key] = {
            "hash": file_hash,
            "platform": parser.platform_name,
            "conversations_count": len(conversations),
            "messages_count": messages_count,
            "last_import": datetime.now().isoformat(),
        }
        self._save_index()

        return FileImportResult(
            file_path=file_path,
            status=status,
            hash=file_hash,
            conversations_count=len(conversations),
            messages_count=messages_count,
            platform=parser.platform_name
        )

    def import_directory(self, directory: Path) -> ImportReport:
        report = ImportReport(started_at=datetime.now())

        if not directory.exists():
            report.ended_at = datetime.now()
            report.errors.append(f"Directory not found: {directory}")
            return report

        supported_exts = {ext for p in self.parsers for ext in p.supported_extensions}

        for file_path in directory.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in supported_exts:
                result = self.import_file(file_path)
                report.file_results.append(result)
                report.files_processed += 1

                if result.status == "new":
                    report.files_new += 1
                elif result.status == "duplicate":
                    report.files_duplicate += 1
                elif result.status == "modified":
                    report.files_modified += 1
                elif result.status == "error":
                    report.files_error += 1
                    if result.error_message:
                        report.errors.append(f"{file_path.name}: {result.error_message}")
                elif result.status == "ignored":
                    report.files_ignored += 1

                report.conversations_imported += result.conversations_count
                report.messages_imported += result.messages_count

        report.ended_at = datetime.now()
        return report

    def import_all(self) -> ImportReport:
        report = ImportReport(started_at=datetime.now())

        dirs = [
            self.config.chatgpt_import_dir,
            self.config.gemini_import_dir,
        ]

        for directory in dirs:
            if directory.exists():
                sub_report = self.import_directory(directory)
                report.files_processed += sub_report.files_processed
                report.files_new += sub_report.files_new
                report.files_duplicate += sub_report.files_duplicate
                report.files_modified += sub_report.files_modified
                report.files_error += sub_report.files_error
                report.files_ignored += sub_report.files_ignored
                report.conversations_imported += sub_report.conversations_imported
                report.messages_imported += sub_report.messages_imported
                report.file_results.extend(sub_report.file_results)
                report.errors.extend(sub_report.errors)

        report.ended_at = datetime.now()
        return report
