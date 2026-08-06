import hashlib
from pathlib import Path


def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    h = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def calculate_quick_hash(file_path: Path) -> str:
    h = hashlib.sha256()
    stat = file_path.stat()
    h.update(str(stat.st_size).encode())
    with open(file_path, "rb") as f:
        h.update(f.read(4096))
    return h.hexdigest()
