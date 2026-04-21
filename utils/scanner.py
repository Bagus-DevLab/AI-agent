"""
utils/scanner.py — Scanner untuk membaca file-file dari sebuah folder.
"""
import os

SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".html", ".css",
    ".json", ".yaml", ".yml", ".md", ".txt", ".sh"
}

SKIP_DIRS = {
    "__pycache__", ".git", "venv", "node_modules",
    "dist", "build", ".venv", "env", "faiss_index"
}

# FIX A: Pola nama file yang dikecualikan dari indexing RAG.
# File-file ini bukan source code — ikut ter-index malah bikin retrieval kacau.
SKIP_FILE_PATTERNS = {
    # Memory & chat history files
    "chat_memory.json",
    "memory.json",
    "temp_cloud.json",
    # Environment & secret files
    ".env",
    ".env.example",
    ".env.local",
    # Lock files — besar dan tidak relevan untuk analisis kode
    "package-lock.json",
    "yarn.lock",
}

# Batas ukuran file: 1MB (hindari OOM untuk file besar)
MAX_FILE_SIZE = 1 * 1024 * 1024


def is_skipped_file(filename: str) -> bool:
    """
    Cek apakah file harus dilewati berdasarkan nama atau pola tertentu.
    Menghindari file memory, secret, dan lock file masuk ke RAG index.
    """
    # Exact match nama file
    if filename in SKIP_FILE_PATTERNS:
        return True
    # Skip semua file yang namanya diawali titik (hidden files: .gitignore, dll)
    if filename.startswith("."):
        return True
    return False


def get_file_list(folder_path):
    """Mengambil daftar path file yang didukung untuk ditampilkan di UI."""
    file_list = []
    for root, dirs, files in os.walk(folder_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for file in files:
            # FIX A: Skip file berdasarkan nama sebelum cek ekstensi
            if is_skipped_file(file):
                continue

            filepath = os.path.join(root, file)
            if os.path.splitext(file)[1].lower() in SUPPORTED_EXTENSIONS:
                try:
                    if os.path.getsize(filepath) <= MAX_FILE_SIZE:
                        file_list.append(filepath)
                except OSError:
                    continue
    return file_list


def scan_workspace(folder_path):
    """
    Membaca konten file dan mengembalikan format yang dibutuhkan RAG.
    Returns: (list[dict], int) — (file data, jumlah file)
    """
    results = []
    file_paths = get_file_list(folder_path)

    for filepath in file_paths:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            results.append({
                "path": filepath,
                "content": content
            })
        except (IOError, OSError) as e:
            print(f"⚠️ Gagal membaca {filepath}: {e}")

    return results, len(results)