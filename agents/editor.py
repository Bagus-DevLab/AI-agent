"""
agents/editor.py — Agent Editor dengan optimasi RAG + Fix B (broad query detection).
Hanya mengambil potongan kode yang relevan untuk menghemat token.
Untuk query umum, inject full file list ke prompt daripada andalkan RAG saja.
"""

import os
import re
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from config import get_llm, get_embeddings, SYSTEM_PROMPT_EDITOR, validate_config
from utils.scanner import scan_workspace, get_file_list
from utils.vectorstore import build_vectorstore, get_retriever

# Base directory project — semua operasi file dibatasi di sini
BASE_DIR = os.path.abspath(os.getcwd())

# FIX B (improved): Deteksi broad query pakai dua lapis filter:
# 1. BROAD_SUBJECTS — kata yang merujuk ke keseluruhan project/file
# 2. BROAD_ACTIONS  — kata yang merujuk ke aksi lihat/jelaskan/tampilkan
# Query dianggap broad kalau mengandung min 1 kata dari SETIAP kelompok,
# ATAU mengandung keyword eksplisit di BROAD_EXPLICIT.

BROAD_SUBJECTS = {
    # Bahasa Indonesia
    "file", "folder", "direktori", "struktur", "project",
    "codebase", "kode", "semua", "seluruh", "keseluruhan",
    "index", "terindex", "di-index", "yang ada", "apa saja",
    # Bahasa Inggris
    "files", "folders", "directory", "structure", "all",
    "entire", "whole", "indexed",
}

BROAD_ACTIONS = {
    # Bahasa Indonesia
    "jelaskan", "tampilkan", "tunjukkan", "lihat", "list",
    "daftar", "rangkum", "ringkas", "ceritakan", "sebutkan",
    "gambarkan", "apa", "berapa",
    # Bahasa Inggris
    "explain", "show", "describe", "summarize",
    "what", "display",
}

# Keyword eksplisit yang langsung trigger broad query tanpa perlu 2 kata
BROAD_EXPLICIT = {
    "overview", "struktur project", "project structure",
    "rangkuman project", "summary project", "semua file",
    "all files", "file list", "daftar file",
}


def is_broad_query(query: str) -> bool:
    """
    Deteksi apakah query bersifat umum/broad menggunakan dua lapis filter.
    Broad = ada kata subjek umum DAN kata aksi, atau keyword eksplisit.
    """
    query_lower = query.lower()

    # Cek keyword eksplisit dulu (paling cepat)
    if any(kw in query_lower for kw in BROAD_EXPLICIT):
        return True

    # Cek kombinasi subjek + aksi
    has_subject = any(word in query_lower for word in BROAD_SUBJECTS)
    has_action = any(word in query_lower for word in BROAD_ACTIONS)
    return has_subject and has_action


def build_file_overview(folder_path: str, docs: list) -> str:
    """
    FIX B: Bangun ringkasan semua file yang ter-index untuk disisipkan ke prompt.
    Menampilkan path + 3 baris pertama tiap file sebagai preview.
    """
    lines = [f"📂 Workspace: {os.path.abspath(folder_path)}",
             f"Total {len(docs)} file ter-index:\n"]

    for doc in docs:
        path = doc["path"]
        # Ambil 3 baris pertama sebagai preview konten
        preview = "\n".join(doc["content"].splitlines()[:3])
        lines.append(f"• {path}\n  {preview[:120]}{'...' if len(preview) > 120 else ''}")

    return "\n".join(lines)


def is_safe_path(filepath: str) -> bool:
    """
    Memastikan filepath target tetap berada di dalam BASE_DIR (Security Sandbox).
    Mencegah path traversal seperti ../../etc/passwd atau path absolut di luar project.
    """
    target_abs = os.path.abspath(filepath)
    return target_abs.startswith(BASE_DIR)


def execute_file_operations(ai_response):
    """Mencari dan mengeksekusi perintah manipulasi file dengan konfirmasi."""
    changes_made = []

    # 1. Logika SAVE
    save_pattern = r"\[SAVE:\s*(.+?)\]\s*```[a-zA-Z]*\n(.*?)```"
    save_matches = re.findall(save_pattern, ai_response, re.DOTALL)
    for filepath, content in save_matches:
        filepath = filepath.strip()

        if not is_safe_path(filepath):
            print(f"🚫 Ditolak: '{filepath}' berada di luar area project. Operasi dibatalkan.")
            continue

        konfirmasi = input(f"\n💾 Simpan perubahan ke '{filepath}'? (y/n): ").strip().lower()
        if konfirmasi == 'y':
            try:
                parent_dir = os.path.dirname(os.path.abspath(filepath))
                os.makedirs(parent_dir, exist_ok=True)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"✅ Berhasil mengupdate {filepath}")
                changes_made.append(f"SAVE: {filepath}")
            except Exception as e:
                print(f"❌ Gagal menyimpan {filepath}: {e}")

    # 2. Logika DELETE
    delete_pattern = r"\[DELETE:\s*(.+?)\]"
    delete_matches = re.findall(delete_pattern, ai_response)
    for filepath in delete_matches:
        filepath = filepath.strip()

        if not is_safe_path(filepath):
            print(f"🚫 Ditolak: '{filepath}' berada di luar area project. Operasi dibatalkan.")
            continue

        konfirmasi = input(f"\n🗑️  Hapus file '{filepath}'? (y/n): ").strip().lower()
        if konfirmasi == 'y' and os.path.exists(filepath):
            os.remove(filepath)
            print(f"✅ Berhasil menghapus {filepath}")
            changes_made.append(f"DELETE: {filepath}")

    return changes_made


def main(folder_path="."):
    print(f"=== 🛠️  AI SMART EDITOR (RAG ENABLED) ===\n📂 Workspace: {folder_path}")

    # FIX #8: Validasi konfigurasi di awal sebelum scan/embedding
    errors = validate_config()
    if errors:
        print("❌ Konfigurasi tidak lengkap:")
        for err in errors:
            print(f"   - {err}")
        return

    # Validasi folder
    if not os.path.isdir(folder_path):
        print(f"❌ Folder tidak ditemukan: {folder_path}")
        return

    # Inisialisasi komponen
    llm = get_llm(temperature=0.2)
    embeddings = get_embeddings()

    # Scan workspace — docs disimpan juga untuk keperluan broad query (Fix B)
    print("📥 Scanning dan indexing kodingan...")
    docs, count = scan_workspace(folder_path)

    if not docs:
        print("❌ Tidak ada file kodingan yang ditemukan di folder ini.")
        return

    vectorstore = build_vectorstore(docs, embeddings)
    retriever = get_retriever(vectorstore, top_k=5)

    chat_history = [SystemMessage(content=SYSTEM_PROMPT_EDITOR)]
    print(f"✅ {count} file berhasil di-index. Siap menerima perintah.")
    print("Ketik 'exit' untuk keluar.\n")

    while True:
        # FIX #6: Tangani EOFError sekalian dengan KeyboardInterrupt
        try:
            user_input = input("\nLu: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Bye!")
            break

        if user_input.lower() in ["exit", "quit"]:
            print("👋 Bye!")
            break
        if not user_input:
            continue

        # FIX B: Deteksi broad query — pakai full file overview bukan RAG
        if is_broad_query(user_input):
            print("📋 Query umum terdeteksi — menggunakan full file overview...")
            context_str = build_file_overview(folder_path, docs)
            prompt = f"DAFTAR LENGKAP FILE DI WORKSPACE:\n{context_str}\n\nINSTRUKSI USER: {user_input}"
        else:
            print("🔍 Mencari referensi kode yang relevan...")
            relevant_chunks = retriever.invoke(user_input)

            context_parts = []
            for doc in relevant_chunks:
                source = doc.metadata.get("source", "unknown")
                context_parts.append(f"// File: {source}\n{doc.page_content}")

            context_str = "\n\n---\n\n".join(context_parts)
            prompt = f"REFERENSI KODE RELEVAN:\n{context_str}\n\nINSTRUKSI USER: {user_input}"

        chat_history.append(HumanMessage(content=prompt))

        print("AI sedang menganalisis...")
        try:
            response = llm.invoke(chat_history)
            ai_text = response.content
            print(f"\nAI:\n{ai_text}\n")

            if execute_file_operations(ai_text):
                print("🔄 Catatan: File telah berubah. Jalankan ulang editor jika ingin refresh index.")

            chat_history.append(AIMessage(content=ai_text))

        except Exception as e:
            print(f"❌ Terjadi kesalahan: {e}")
            # FIX #7: Pop HumanMessage terakhir agar history tidak corrupt
            chat_history.pop()


if __name__ == "__main__":
    main()