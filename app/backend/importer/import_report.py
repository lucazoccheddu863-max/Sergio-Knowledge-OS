from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any


@dataclass
class FileImportResult:
    file_path: Path
    status: str = "pending"
    conversations_count: int = 0
    messages_count: int = 0
    hash: Optional[str] = None
    error_message: Optional[str] = None
    platform: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ImportReport:
    started_at: datetime
    ended_at: Optional[datetime] = None
    files_processed: int = 0
    files_new: int = 0
    files_duplicate: int = 0
    files_modified: int = 0
    files_error: int = 0
    files_ignored: int = 0
    conversations_imported: int = 0
    messages_imported: int = 0
    errors: List[str] = field(default_factory=list)
    file_results: List[FileImportResult] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        if self.ended_at is None:
            return 0.0
        return (self.ended_at - self.started_at).total_seconds()

    @property
    def success_rate(self) -> float:
        if self.files_processed == 0:
            return 0.0
        successful = self.files_processed - self.files_error - self.files_ignored
        return (successful / self.files_processed) * 100

    def __str__(self) -> str:
        lines = [
            "Import Report",
            "=" * 40,
            f"Files processed: {self.files_processed}",
            f"  New:       {self.files_new}",
            f"  Duplicate: {self.files_duplicate}",
            f"  Modified:  {self.files_modified}",
            f"  Error:     {self.files_error}",
            f"  Ignored:   {self.files_ignored}",
            f"Conversations: {self.conversations_imported}",
            f"Messages:      {self.messages_imported}",
            f"Duration:      {self.duration_seconds:.3f}s",
            f"Success rate:  {self.success_rate:.1f}%",
        ]
        if self.errors:
            lines.append("\nErrors:")
            for err in self.errors:
                lines.append(f"  - {err}")
        return "\n".join(lines)
