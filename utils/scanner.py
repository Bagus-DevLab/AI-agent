"""
utils/scanner.py — File scanner untuk workspace codebase.

Scan rekursif folder workspace, baca file source code yang relevan,
dan return hasilnya untuk embedding/indexing RAG.
"""

import os
from typing import TypedDict


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class ScannedFile(TypedDict):
    """Struktur data untuk file hasil scan workspace."""
    path: str
    content: str


# ---------------------------------------------------------------------------
# Constants — Skip Rules
# ---------------------------------------------------------------------------

SKIP_FILE_PATTERNS: set[str] = {
    # Memory & chat history
    "chat_memory.json",
    "memory.json",
    "temp_cloud.json",
    # Environment & secrets
    ".env",
    ".env.example",
    ".env.local",
    # Lock files
    "package-lock.json",
    "yarn.lock",
}

SKIP_FILE_PREFIXES: list[tuple[str, str]] = [
    ("editor_", ".json"),
    ("rag_", ".json"),
    ("memory_", ".json"),
]

SKIP_DIRS: set[str] = {
    "node_modules", ".git", "__pycache__",
    "venv", ".venv", "env", ".env",
    "dist", "build", ".next", ".nuxt",
    "faiss_index", ".idea", ".vscode",
    "vendor", "target", ".tox",
    "htmlcov", ".mypy_cache", ".pytest_cache", "egg-info",
}

SUPPORTED_EXTENSIONS: set[str] = {
    # Python, JS/TS
    ".py", ".js", ".ts", ".jsx", ".tsx",
    # Other languages
    ".java", ".go", ".rs", ".rb", ".php",
    ".c", ".cpp", ".h", ".hpp", ".cs",
    ".swift", ".kt", ".scala", ".lua",
    # Shell
    ".sh", ".bash", ".zsh", ".fish",
    # Web
    ".html", ".css", ".scss", ".sass", ".less",
    # Data/Query
    ".sql", ".graphql", ".gql",
    ".yaml", ".yml", ".toml",
    # Docs
    ".md", ".txt", ".rst",
    # Config
    ".json", ".xml", ".csv",
    ".dockerfile", ".makefile",
    ".gitignore", ".env.example",
    ".cfg", ".ini", ".conf",
}

MAX_FILE_SIZE: int = 1_000_000  # 1MB


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

def should_skip_file(filename: str) -> bool:
    """
    Cek apakah file harus di-skip dari scanning.

    Rules:
      1. Exact match dengan SKIP_FILE_PATTERNS
      2. Semua varian .env (.env, .env.*)
      3. Prefix+suffix match dengan SKIP_FILE_PREFIXES
    """
    if filename in SKIP_FILE_PATTERNS:
        return True

    if filename == ".env" or filename.startswith(".env."):
        return True

    for prefix, suffix in SKIP_FILE_PREFIXES:
        if filename.startswith(prefix) and filename.endswith(suffix):
            return True

    return False


def _is_valid_file(filename: str) -> bool:
    """Cek apakah file layak di-scan (bukan hidden, bukan skip, ekstensi valid)."""
    if filename.startswith("."):
        return False
    if should_skip_file(filename):
        return False
    _, ext = os.path.splitext(filename)
    return ext.lower() in SUPPORTED_EXTENSIONS


def _filter_dirs(dirs: list[str]) -> list[str]:
    """Filter direktori yang tidak perlu di-scan."""
    return [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]


def _make_relative_path(filepath: str, base: str) -> str:
    """Buat path relatif dengan prefix './'."""
    rel = os.path.relpath(filepath, base)
    return rel if rel.startswith(".") else f"./{rel}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scan_workspace(folder_path: str = ".") -> tuple[list[ScannedFile], int]:
    """
    Scan direktori secara rekursif dan baca semua file source code.

    Returns:
        (list of ScannedFile dicts, jumlah file yang berhasil di-scan)
    """
    results: list[ScannedFile] = []
    folder_path = os.path.abspath(folder_path)

    for root, dirs, files in os.walk(folder_path):
        dirs[:] = _filter_dirs(dirs)

        for filename in files:
            if not _is_valid_file(filename):
                continue

            filepath = os.path.join(root, filename)

            # Skip file terlalu besar
            try:
                if os.path.getsize(filepath) > MAX_FILE_SIZE:
                    continue
            except OSError:
                continue

            # Baca file
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                rel_path = _make_relative_path(filepath, folder_path)
                results.append({"path": rel_path, "content": content})
            except (IOError, OSError, UnicodeDecodeError):
                continue

    return results, len(results)


def get_file_list(folder_path: str = ".") -> list[str]:
    """
    Ambil daftar path semua file valid di workspace.
    Menggunakan filter yang sama dengan scan_workspace.
    """
    file_paths: list[str] = []
    folder_path = os.path.abspath(folder_path)

    for root, dirs, files in os.walk(folder_path):
        dirs[:] = _filter_dirs(dirs)

        for filename in files:
            if not _is_valid_file(filename):
                continue

            filepath = os.path.join(root, filename)

            try:
                if os.path.getsize(filepath) > MAX_FILE_SIZE:
                    continue
            except OSError:
                continue

            file_paths.append(_make_relative_path(filepath, folder_path))

    return file_paths
