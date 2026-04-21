"""
scanner.py — Modul untuk scanning folder kodingan secara dinamis.
Digunakan oleh agent_rag dan agent_edit.
"""

import os
from langchain_community.document_loaders import TextLoader
from config import FORBIDDEN_DIRS, ALLOWED_EXTS


def scan_workspace(folder_path="."):
    """
    Scan seluruh file kodingan di folder secara rekursif.
    Menghindari folder terlarang dan hanya membaca ekstensi yang diizinkan.
    
    Args:
        folder_path: Path root folder yang akan di-scan
        
    Returns:
        tuple: (docs, file_count) — list dokumen dan jumlah file yang berhasil dibaca
    """
    docs = []
    file_count = 0

    for root, dirs, files in os.walk(folder_path):
        # Filter folder terlarang SEBELUM masuk ke dalamnya
        dirs[:] = [d for d in dirs if d not in FORBIDDEN_DIRS]

        for file_name in files:
            _, ext = os.path.splitext(file_name)
            if ext.lower() not in ALLOWED_EXTS:
                continue

            file_path = os.path.join(root, file_name)
            try:
                loader = TextLoader(file_path, encoding="utf-8")
                loaded_docs = loader.load()

                # Tambahkan metadata path ke setiap dokumen
                for doc in loaded_docs:
                    doc.metadata["source"] = file_path

                docs.extend(loaded_docs)
                file_count += 1
            except Exception as e:
                print(f"  ⚠️ Gagal baca {file_path}: {e}")

    return docs, file_count


def get_file_list(folder_path="."):
    """
    Mendapatkan daftar file kodingan tanpa membaca isinya.
    Berguna untuk menampilkan workspace overview.
    
    Args:
        folder_path: Path root folder
        
    Returns:
        list: Daftar path file yang ditemukan
    """
    file_list = []

    for root, dirs, files in os.walk(folder_path):
        dirs[:] = [d for d in dirs if d not in FORBIDDEN_DIRS]

        for file_name in files:
            _, ext = os.path.splitext(file_name)
            if ext.lower() in ALLOWED_EXTS:
                file_path = os.path.join(root, file_name)
                file_list.append(file_path)

    return sorted(file_list)
