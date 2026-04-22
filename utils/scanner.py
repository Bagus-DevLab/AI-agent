"""
utils/scanner.py — File Scanner untuk Workspace Codebase
=========================================================

Modul ini bertanggung jawab untuk melakukan **recursive directory scan**
terhadap folder workspace dan membaca seluruh file source code yang relevan.
Hasil scan digunakan sebagai input untuk proses embedding dan indexing RAG.

Fitur utama:
    - Recursive scan dengan filter ekstensi file yang didukung
    - Auto-skip direktori non-relevan (node_modules, .git, venv, dll.)
    - Auto-skip file non-code (lock files, .env, memory files, dll.)
    - Auto-skip hidden files (diawali titik)
    - Batas ukuran file 1MB untuk mencegah out-of-memory
    - Penanganan error graceful untuk file yang tidak bisa dibaca
"""

import os
from typing import TypedDict


class ScannedFile(TypedDict):
    """Struktur data untuk file hasil scan workspace."""
    path: str
    content: str

# ============================================================================
# 🚫 KONSTANTA — FILE YANG DI-SKIP (EXACT MATCH)
# ============================================================================
# File-file ini bukan source code yang relevan untuk analisis.
# Jika ikut ter-index, justru akan mengacaukan hasil retrieval RAG.

SKIP_FILE_PATTERNS: set[str] = {
    # Memory & chat history — data runtime, bukan kode
    "chat_memory.json",
    "memory.json",
    "temp_cloud.json",
    # Environment & secret — mengandung API key, TIDAK BOLEH ter-index
    ".env",
    ".env.example",
    ".env.local",
    # Lock files — sangat besar dan tidak relevan untuk analisis kode
    "package-lock.json",
    "yarn.lock",
}

# ============================================================================
# 🚫 KONSTANTA — PREFIX FILE YANG DI-SKIP (PATTERN MATCH)
# ============================================================================
# File dengan prefix tertentu yang bukan source code.
# Contoh: editor_belajar_langchain.json, editor_myproject.json, dll.
# Nama file ini dinamis (berdasarkan nama project), jadi tidak bisa exact match.

SKIP_FILE_PREFIXES: list[tuple[str, str]] = [
    # (prefix, suffix) — file yang match keduanya akan di-skip
    ("editor_", ".json"),    # Memory file dari editor agent
    ("rag_", ".json"),       # Memory file dari rag agent (jika ada)
    ("memory_", ".json"),    # Memory file dari memory agent (jika ada)
]


# ============================================================================
# 📁 KONSTANTA — DIREKTORI YANG DI-SKIP
# ============================================================================

SKIP_DIRS: set[str] = {
    "node_modules",
    ".git",
    "__pycache__",
    "venv",
    ".venv",
    "env",
    ".env",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "faiss_index",
    ".idea",
    ".vscode",
    "vendor",
    "target",
    ".tox",
    "htmlcov",
    ".mypy_cache",
    ".pytest_cache",
    "egg-info",
}


# ============================================================================
# 📄 KONSTANTA — EKSTENSI FILE YANG DIDUKUNG
# ============================================================================

SUPPORTED_EXTENSIONS: set[str] = {
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".java", ".go", ".rs", ".rb", ".php",
    ".c", ".cpp", ".h", ".hpp", ".cs",
    ".swift", ".kt", ".scala", ".lua",
    ".sh", ".bash", ".zsh", ".fish",
    ".html", ".css", ".scss", ".sass", ".less",
    ".sql", ".graphql", ".gql",
    ".yaml", ".yml", ".toml",
    ".md", ".txt", ".rst",
    ".json",  # JSON source code (config files, dll)
    ".xml", ".csv",
    ".dockerfile", ".makefile",
    ".gitignore", ".env.example",
    ".cfg", ".ini", ".conf",
}

# Batas ukuran file (1MB)
MAX_FILE_SIZE: int = 1_000_000


# ============================================================================
# 🔧 FUNGSI HELPER
# ============================================================================

def should_skip_file(filename: str) -> bool:
    """
    Cek apakah file harus di-skip dari scanning.

    Mengecek tiga hal:
    1. Exact match dengan SKIP_FILE_PATTERNS
    2. Semua varian .env (`.env`, `.env.*`) — mencegah kebocoran secret
    3. Prefix+suffix match dengan SKIP_FILE_PREFIXES

    Args:
        filename: Nama file (tanpa path, hanya basename)

    Returns:
        True jika file harus di-skip, False jika boleh di-scan
    """
    # 1. Exact match
    if filename in SKIP_FILE_PATTERNS:
        return True

    # 2. Skip semua varian .env (e.g. .env.production, .env.staging, dll.)
    if filename == ".env" or filename.startswith(".env."):
        return True

    # 3. Prefix + suffix pattern match
    for prefix, suffix in SKIP_FILE_PREFIXES:
        if filename.startswith(prefix) and filename.endswith(suffix):
            return True

    return False


# ============================================================================
# 🔍 FUNGSI UTAMA — SCAN DIRECTORY
# ============================================================================

def scan_workspace(folder_path: str = ".") -> tuple[list[ScannedFile], int]:
    """
    Scan direktori secara rekursif dan baca semua file source code.

    Args:
        folder_path: Path ke folder yang akan di-scan (default: current dir)

    Returns:
        Tuple berisi:
        - list[ScannedFile]: List of {"path": relative_path, "content": file_content}
        - int: Jumlah file yang berhasil di-scan
    """
    results: list[ScannedFile] = []
    folder_path = os.path.abspath(folder_path)

    for root, dirs, files in os.walk(folder_path):
        # Filter direktori — modifikasi in-place agar os.walk tidak masuk
        dirs[:] = [
            d for d in dirs
            if d not in SKIP_DIRS and not d.startswith(".")
        ]

        for filename in files:
            # Skip hidden files
            if filename.startswith("."):
                continue

            # Skip file berdasarkan nama (exact + pattern match)
            if should_skip_file(filename):
                continue

            # Cek ekstensi
            _, ext = os.path.splitext(filename)
            if ext.lower() not in SUPPORTED_EXTENSIONS:
                continue

            filepath = os.path.join(root, filename)

            # Cek ukuran file
            try:
                if os.path.getsize(filepath) > MAX_FILE_SIZE:
                    continue
            except OSError:
                continue

            # Baca file
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Buat path relatif
                rel_path = os.path.relpath(filepath, folder_path)
                if not rel_path.startswith("."):
                    rel_path = f"./{rel_path}"

                results.append({"path": rel_path, "content": content})
                
            except (IOError, OSError, UnicodeDecodeError):
                # Skip file yang tidak bisa dibaca
                continue

    return results, len(results)

def get_file_list(folder_path: str = ".") -> list[str]:
    """
    Mengambil daftar path semua file yang valid di dalam workspace.
    Menggunakan filter yang sama dengan scan_workspace.
    """
    file_paths: list[str] = []
    folder_path = os.path.abspath(folder_path)

    for root, dirs, files in os.walk(folder_path):
        # Filter direktori (sama seperti scan_workspace)
        dirs[:] = [
            d for d in dirs
            if d not in SKIP_DIRS and not d.startswith(".")
        ]

        for filename in files:
            # Lewati file sesuai aturan
            if filename.startswith("."): continue
            if should_skip_file(filename): continue

            # Cek ekstensi
            _, ext = os.path.splitext(filename)
            if ext.lower() not in SUPPORTED_EXTENSIONS: continue

            # Catat path-nya
            filepath = os.path.join(root, filename)

            # Cek ukuran file (konsisten dengan scan_workspace)
            try:
                if os.path.getsize(filepath) > MAX_FILE_SIZE:
                    continue
            except OSError:
                continue

            rel_path = os.path.relpath(filepath, folder_path)
            
            if not rel_path.startswith("."):
                rel_path = f"./{rel_path}"

            file_paths.append(rel_path)

    return file_paths