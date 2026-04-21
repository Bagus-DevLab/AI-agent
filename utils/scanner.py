"""
utils/scanner.py — Scanner untuk membaca file-file dari sebuah folder.
Digunakan oleh RAG agent untuk indexing codebase.
"""

import os

# Ekstensi file yang didukung untuk scanning
SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".java", ".go", ".rs", ".cpp", ".c", ".h",
    ".html", ".css", ".scss",
    ".json", ".yaml", ".yml", ".toml",
    ".md", ".txt", ".rst",
    ".sh", ".bash", ".zsh",
    ".sql", ".graphql",
    ".dockerfile", ".env.example",
}

# Folder yang di-skip saat scanning
SKIP_DIRS = {
    "__pycache__", ".git", ".venv", "venv", "env",
    "node_modules", ".next", "dist", "build",
    ".idea", ".vscode", ".mypy_cache", ".pytest_cache",
    "egg-info", ".eggs", ".tox",
}

# File yang di-skip
SKIP_FILES = {
    ".env", ".env.local", ".DS_Store", "Thumbs.db",
    "package-lock.json", "yarn.lock", "poetry.lock",
}

# Batas ukuran file (500KB)
MAX_FILE_SIZE = 500 * 1024


def scan_folder(folder_path: str) -> list[dict]:
    """
    Scan folder dan return list of dict berisi path + content file.
    
    Args:
        folder_path: Path ke folder yang mau di-scan
        
    Returns:
        List of {"path": str, "content": str}
        
    Raises:
        FileNotFoundError: Jika folder tidak ditemukan
        NotADirectoryError: Jika path bukan folder
    """
    # Validasi path
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Path tidak ditemukan: {folder_path}")
    if not os.path.isdir(folder_path):
        raise NotADirectoryError(f"Path bukan folder: {folder_path}")

    results = []
    skipped_count = 0

    for root, dirs, files in os.walk(folder_path):
        # Filter out skip directories (in-place untuk os.walk)
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]

        for filename in files:
            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, folder_path)

            # Skip file tertentu
            if filename in SKIP_FILES:
                skipped_count += 1
                continue

            # Cek ekstensi
            _, ext = os.path.splitext(filename)
            if ext.lower() not in SUPPORTED_EXTENSIONS and filename not in ("Dockerfile", "Makefile", "Procfile"):
                skipped_count += 1
                continue

            # Cek ukuran file
            try:
                file_size = os.path.getsize(filepath)
                if file_size > MAX_FILE_SIZE:
                    print(f"   ⏭️  Skip (terlalu besar): {rel_path} ({file_size // 1024}KB)")
                    skipped_count += 1
                    continue
                if file_size == 0:
                    skipped_count += 1
                    continue
            except OSError:
                skipped_count += 1
                continue

            # Baca file
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                results.append({
                    "path": rel_path,
                    "content": content,
                })
            except Exception as e:
                print(f"   ⚠️  Gagal baca: {rel_path} ({e})")
                skipped_count += 1

    if skipped_count > 0:
        print(f"   ℹ️  {skipped_count} file di-skip (tidak relevan/terlalu besar)")

    return results
