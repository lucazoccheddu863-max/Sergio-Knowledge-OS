import os
from pathlib import Path
from typing import Optional, Any, Dict
import yaml


class Config:
    _instance: Optional["Config"] = None

    def __init__(self, data: Dict[str, Any], base_path: Path):
        self._data = data
        self._base_path = base_path.resolve()

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Config":
        if cls._instance is not None:
            return cls._instance

        if config_path is None:
            current = Path(__file__).resolve()
            project_root = current.parent.parent.parent
            config_path = project_root / "config.yaml"

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        base_path = config_path.parent
        cls._instance = cls(data, base_path)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "Config":
        if cls._instance is None:
            return cls.load()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        cls._instance = None

    def _resolve_path(self, key: str) -> Path:
        raw = self._data.get(key, "")
        path = Path(raw)
        if path.is_absolute():
            return path
        return (self._base_path / path).resolve()

    @property
    def database_path(self) -> Path:
        return self._resolve_path("database_path")

    @property
    def archive_root(self) -> Path:
        return self._resolve_path("archive_root")

    @property
    def chatgpt_import_dir(self) -> Path:
        return self._resolve_path("chatgpt_import_dir")

    @property
    def gemini_import_dir(self) -> Path:
        return self._resolve_path("gemini_import_dir")

    @property
    def backup_dir(self) -> Path:
        return self._resolve_path("backup_dir")

    @property
    def hash_algorithm(self) -> str:
        return self._data.get("hash_algorithm", "sha256")

    @property
    def ai_primary_provider(self) -> str:
        return self._data.get("ai_primary_provider", "openai")

    @property
    def ai_local_model(self) -> str:
        return self._data.get("ai_local_model", "qwen2.5:1.5b")

    def ensure_directories(self) -> None:
        for path in [
            self.database_path.parent,
            self.archive_root,
            self.chatgpt_import_dir,
            self.gemini_import_dir,
            self.backup_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)
