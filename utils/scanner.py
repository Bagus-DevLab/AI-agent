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

Penggunaan:
    >>> from utils.scanner import scan_workspace, get_file_list
    >>>
    >>> # Mendapatkan daftar path file saja
    >>> files = get_file_list("./my_project")
    >>> print(f"Ditemukan {len(files)} file")
    >>>
    >>> # Mendapatkan path + konten file untuk RAG
    >>> file_data, count = scan_workspace("./my_project")
    >>> for item in file_data:
    ...     print(f"{item['path']} — {len(item['content'])} chars")
"""

import os
from typing import TypedDict

# ============================================================================
# 📋 KONSTANTA — EKSTENSI FILE YANG DIDUKUNG
# ============================================================================
# Hanya file dengan ekstensi berikut yang akan di-scan dan di-index.
# Ekstensi dipilih berdasarkan file source code dan konfigurasi yang umum
# ditemukan di project software.

SUPPORTED_EXTENSIONS: set[str] = {
    # Python
    ".py",
    # JavaScript / TypeScript
    ".js", ".ts", ".jsx", ".tsx",
    # Go
    ".go",
    # Web (markup & styling)
    ".html", ".css",
    # Data & konfigurasi
    ".json", ".yaml", ".yml",
    # Dokumentasi & scripting
    ".md", ".txt", ".sh",
}

# ============================================================================
# 🚫 KONSTANTA — DIREKTORI YANG DI-SKIP
# ============================================================================
# Direktori-direktori ini akan sepenuhnya diabaikan saat recursive scan.
# Alasan utama: ukuran besar, bukan source code asli, atau file generated.

SKIP_DIRS: set[str] = {
    # Python environments & cache
    "venv", ".venv", "env", "__pycache__",
    # Version control
    ".git",
    # Node.js dependencies
    "node_modules",
    # Build output & artifacts
    "dist", "build",
    # FAISS index (generated oleh aplikasi ini sendiri)
    "faiss_index",
}

# ============================================================================
# 🚫 KONSTANTA — FILE YANG DI-SKIP
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
# 📏 KONSTANTA — BATAS UKURAN FILE
# ============================================================================
# File yang melebihi batas ini akan di-skip untuk mencegah out-of-memory
# saat proses pembacaan dan embedding.

MAX_FILE_SIZE: int = 1 * 1024 * 1024  # 1 MB


# ============================================================================
# 📦 TYPE DEFINITIONS
# ============================================================================

class FileData(TypedDict):
    """
    Struktur data untuk hasil scan satu file.

    Attributes:
        path (str): Path absolut atau relatif ke file.
        content (str): Seluruh isi/konten teks dari file.
    """
    path: str
    content: str


# ============================================================================
# 🔧 HELPER FUNCTIONS
# ============================================================================

def is_skipped_file(filename: str) -> bool:
    """
    Cek apakah sebuah file harus dilewati (tidak di-scan).

    File akan di-skip jika memenuhi salah satu kondisi:
        1. Nama file cocok persis dengan salah satu entry di SKIP_FILE_PATTERNS
           (contoh: "package-lock.json", ".env", "memory.json")
        2. Nama file diawali dengan titik (hidden file di Unix/macOS)
           (contoh: ".gitignore", ".dockerignore", ".eslintrc")

    Args:
        filename (str): Nama file saja (tanpa path direktori).
            Contoh: "scanner.py", ".env", "package-lock.json"

    Returns:
        bool: True jika file harus di-skip, False jika boleh di-scan.

    Contoh:
        >>> is_skipped_file("scanner.py")
        False
        >>> is_skipped_file(".env")
        True
        >>> is_skipped_file("package-lock.json")
        True
        >>> is_skipped_file(".gitignore")
        True
        >>> is_skipped_file("README.md")
        False
    """
    # Exact match: cek apakah nama file ada di daftar skip
    if filename in SKIP_FILE_PATTERNS:
        return True

    # Hidden files: skip semua file yang diawali titik
    # (kecuali yang sudah ditangani exact match di atas)
    if filename.startswith("."):
        return True

    return False


def _has_supported_extension(filename: str) -> bool:
    """
    Cek apakah file memiliki ekstensi yang didukung untuk di-scan.

    Pengecekan dilakukan secara case-insensitive sehingga file dengan
    ekstensi ".PY", ".Py", atau ".py" semuanya akan dianggap valid.

    Args:
        filename (str): Nama file (dengan ekstensi).
            Contoh: "main.py", "App.TSX", "config.YAML"

    Returns:
        bool: True jika ekstensi file didukung, False jika tidak.

    Contoh:
        >>> _has_supported_extension("main.py")
        True
        >>> _has_supported_extension("image.png")
        False
        >>> _has_supported_extension("App.TSX")
        True
    """
    _, ext = os.path.splitext(filename)
    return ext.lower() in SUPPORTED_EXTENSIONS


def _is_within_size_limit(filepath: str) -> bool:
    """
    Cek apakah ukuran file tidak melebihi batas maksimum (MAX_FILE_SIZE).

    Fungsi ini juga menangani error OS (misal: file terhapus antara
    saat listing dan saat pengecekan ukuran) secara graceful.

    Args:
        filepath (str): Path lengkap ke file yang akan dicek.

    Returns:
        bool: True jika file berukuran <= MAX_FILE_SIZE, False jika
              melebihi batas atau terjadi error saat membaca ukuran.

    Contoh:
        >>> _is_within_size_limit("./small_file.py")    # 500 bytes
        True
        >>> _is_within_size_limit("./huge_bundle.js")   # 5 MB
        False
    """
    try:
        return os.path.getsize(filepath) <= MAX_FILE_SIZE
    except OSError:
        return False


def _read_file_content(filepath: str) -> str | None:
    """
    Membaca seluruh konten teks dari sebuah file.

    File dibaca dengan encoding UTF-8 dan error karakter yang tidak
    valid akan diabaikan (errors="ignore") untuk mencegah crash pada
    file yang mengandung karakter non-UTF-8.

    Args:
        filepath (str): Path lengkap ke file yang akan dibaca.

    Returns:
        str | None: Isi file sebagai string jika berhasil dibaca,
                    atau None jika terjadi error I/O.

    Contoh:
        >>> content = _read_file_content("./utils/scanner.py")
        >>> if content is not None:
        ...     print(f"Berhasil membaca {len(content)} karakter")
    """
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except (IOError, OSError) as e:
        print(f"⚠️ Gagal membaca {filepath}: {e}")
        return None


# ============================================================================
# 📂 FUNGSI UTAMA — PUBLIC API
# ============================================================================

def get_file_list(folder_path: str) -> list[str]:
    """
    Mengambil daftar path file yang didukung dari sebuah folder secara rekursif.

    Fungsi ini melakukan recursive walk pada folder_path dan mengumpulkan
    semua file yang memenuhi kriteria berikut:
        1. Tidak berada di dalam direktori yang di-skip (SKIP_DIRS)
        2. Bukan file yang masuk daftar skip (SKIP_FILE_PATTERNS / hidden files)
        3. Memiliki ekstensi yang didukung (SUPPORTED_EXTENSIONS)
        4. Ukuran file tidak melebihi MAX_FILE_SIZE (1MB)

    Args:
        folder_path (str): Path ke folder root yang akan di-scan.
            Bisa berupa path absolut atau relatif.
            Contoh: ".", "./src", "/home/user/project"

    Returns:
        list[str]: Daftar path absolut ke file-file yang memenuhi kriteria.
            List kosong jika tidak ada file yang ditemukan atau folder tidak ada.

    Catatan:
        - Urutan file dalam list tidak dijamin konsisten antar OS.
        - Symbolic link akan diikuti (default behavior os.walk).
        - Direktori di SKIP_DIRS akan di-prune sehingga subdirektorinya
          juga tidak akan di-scan (efisien untuk node_modules yang besar).

    Contoh:
        >>> files = get_file_list("./my_project")
        >>> print(f"Ditemukan {len(files)} file source code")
        Ditemukan 42 file source code
        >>> for f in files[:3]:
        ...     print(f)
        ./my_project/main.py
        ./my_project/utils/helper.py
        ./my_project/config.yaml
    """
    file_list: list[str] = []

    for root, dirs, files in os.walk(folder_path):
        # Prune: modifikasi dirs in-place agar os.walk tidak masuk
        # ke direktori yang di-skip. Ini jauh lebih efisien daripada
        # mengecek setiap file di dalam direktori tersebut.
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for filename in files:
            # Filter 1: Skip file berdasarkan nama/pola
            if is_skipped_file(filename):
                continue

            # Filter 2: Skip file dengan ekstensi yang tidak didukung
            if not _has_supported_extension(filename):
                continue

            # Filter 3: Skip file yang terlalu besar
            filepath: str = os.path.join(root, filename)
            if not _is_within_size_limit(filepath):
                continue

            file_list.append(filepath)

    return file_list


def scan_workspace(folder_path: str) -> tuple[list[FileData], int]:
    """
    Scan workspace dan baca konten semua file source code yang relevan.

    Fungsi utama yang menggabungkan proses listing file (get_file_list)
    dengan pembacaan konten. Hasilnya digunakan sebagai input untuk
    proses embedding dan indexing di vector store (RAG pipeline).

    Alur kerja:
        1. Panggil get_file_list() untuk mendapatkan daftar file valid
        2. Baca konten setiap file satu per satu
        3. File yang gagal dibaca akan di-skip (dengan warning ke console)
        4. Kembalikan list of dict berisi path + content

    Args:
        folder_path (str): Path ke folder root workspace yang akan di-scan.
            Contoh: ".", "./src", "/home/user/project"

    Returns:
        tuple[list[FileData], int]: Tuple berisi dua elemen:
            - list[FileData]: List of dict, setiap dict berisi:
                - "path" (str): Path ke file
                - "content" (str): Seluruh isi teks file
            - int: Jumlah total file yang berhasil dibaca.

    Contoh:
        >>> file_data, count = scan_workspace("./my_project")
        >>> print(f"Berhasil membaca {count} file")
        Berhasil membaca 42 file
        >>>
        >>> for item in file_data[:2]:
        ...     print(f"{item['path']} — {len(item['content'])} chars")
        ./my_project/main.py — 1523 chars
        ./my_project/utils/helper.py — 892 chars
    """
    results: list[FileData] = []
    file_paths: list[str] = get_file_list(folder_path)

    for filepath in file_paths:
        content: str | None = _read_file_content(filepath)

        # Skip file yang gagal dibaca (warning sudah dicetak di _read_file_content)
        if content is None:
            continue

        results.append({
            "path": filepath,
            "content": content,
        })

    return results, len(results)