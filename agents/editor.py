"""
agents/editor.py — Agent Editor dengan optimasi RAG + Fix B (broad query detection) 
+ Fix C (Direct File Focus) + Auto-Refresh Index.
"""

import os
import re
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from config import get_llm, get_embeddings, SYSTEM_PROMPT_EDITOR, validate_config
from utils.scanner import scan_workspace, get_file_list
from utils.vectorstore import build_vectorstore, get_retriever

# Base directory project — semua operasi file dibatasi di sini
BASE_DIR = os.path.abspath(os.getcwd())

# ==========================================
# FILTER DETEKSI QUERY UMUM (BROAD QUERY)
# ==========================================
BROAD_SUBJECTS = {
    "file", "folder", "direktori", "struktur", "project",
    "codebase", "kode", "semua", "seluruh", "keseluruhan",
    "index", "terindex", "di-index", "yang ada", "apa saja",
    "files", "folders", "directory", "structure", "all",
    "entire", "whole", "indexed",
}

BROAD_ACTIONS = {
    "jelaskan", "tampilkan", "tunjukkan", "lihat", "list",
    "daftar", "rangkum", "ringkas", "ceritakan", "sebutkan",
    "gambarkan", "apa", "berapa",
    "explain", "show", "describe", "summarize",
    "what", "display",
}

BROAD_EXPLICIT = {
    "overview", "struktur project", "project structure",
    "rangkuman project", "summary project", "semua file",
    "all files", "file list", "daftar file",
}


def is_broad_query(query: str) -> bool:
    """Deteksi apakah query bersifat umum/broad."""
    query_lower = query.lower()
    if any(kw in query_lower for kw in BROAD_EXPLICIT):
        return True
    has_subject = any(word in query_lower for word in BROAD_SUBJECTS)
    has_action = any(word in query_lower for word in BROAD_ACTIONS)
    return has_subject and has_action


def find_mentioned_files(query: str, docs: list) -> list:
    """
    Mencari apakah user menyebutkan nama file secara spesifik di prompt.
    Jika ya, kembalikan seluruh isi file tersebut agar AI tidak halu.
    """
    mentioned = []
    query_lower = query.lower()
    
    for doc in docs:
        # Ambil nama file saja (misal: "readme.md" dari "./readme.md")
        filename = os.path.basename(doc["path"]).lower()
        if filename in query_lower:
            mentioned.append(doc)
            
    return mentioned


def build_file_overview(folder_path: str, docs: list) -> str:
    """Bangun ringkasan semua file (hanya preview 3 baris) untuk broad query."""
    lines = [f"📂 Workspace: {os.path.abspath(folder_path)}",
             f"Total {len(docs)} file ter-index:\n"]

    for doc in docs:
        path = doc["path"]
        preview = "\n".join(doc["content"].splitlines()[:3])
        lines.append(f"• {path}\n  {preview[:120]}{'...' if len(preview) > 120 else ''}")

    return "\n".join(lines)


def is_safe_path(filepath: str) -> bool:
    """Memastikan filepath target tetap berada di dalam BASE_DIR (Anti Path-Traversal)."""
    target_abs = os.path.abspath(filepath)
    return target_abs.startswith(BASE_DIR)


def extract_save_blocks(ai_response: str):
    """Parser yang lebih tangguh terhadap self-quoting dan format markdown."""
    results = []
    
    # 1. Regex ini mencari [SAVE: path] di awal baris
    # 2. Mengambil semua konten (re.DOTALL)
    # 3. Berhenti HANYA pada [/SAVE] yang berada tepat di awal baris baru
    pattern = r'^\[SAVE:\s*(.+?)\]\n(.*?)\n^\[/SAVE\]'
    matches = re.finditer(pattern, ai_response, re.DOTALL | re.MULTILINE)

    for match in matches:
        filepath = match.group(1).strip()
        content = match.group(2).strip()

        # Bersihkan pembungkus markdown (```) jika AI menambahkannya
        if content.startswith("```"):
            content = re.sub(r'^```\w*\n', '', content)
            if content.endswith("```"):
                content = content[:-3].strip()

        results.append((filepath, content))
        
    return results


def execute_file_operations(ai_response):
    """Mencari dan mengeksekusi perintah manipulasi file dengan konfirmasi."""
    changes_made = []

    # 1. Eksekusi perintah SAVE
    save_matches = extract_save_blocks(ai_response)
    for filepath, file_content in save_matches:
        filepath = filepath.strip()

        if not is_safe_path(filepath):
            print(f"🚫 Ditolak: '{filepath}' berada di luar area project.")
            continue

        konfirmasi = input(f"\n💾 Simpan perubahan ke '{filepath}'? (y/n): ").strip().lower()
        if konfirmasi == 'y':
            try:
                parent_dir = os.path.dirname(os.path.abspath(filepath))
                if parent_dir:
                    os.makedirs(parent_dir, exist_ok=True)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(file_content)
                print(f"✅ Berhasil mengupdate {filepath}")
                changes_made.append(f"SAVE: {filepath}")
            except Exception as e:
                print(f"❌ Gagal menyimpan {filepath}: {e}")

    # 2. Eksekusi perintah DELETE
    delete_pattern = r"^\[DELETE:\s*(.+?)\]"
    delete_matches = re.findall(delete_pattern, ai_response, re.MULTILINE)    
    for filepath in delete_matches:
        filepath = filepath.strip()

        if not is_safe_path(filepath):
            print(f"🚫 Ditolak: '{filepath}' berada di luar area project.")
            continue

        konfirmasi = input(f"\n🗑️  Hapus file '{filepath}'? (y/n): ").strip().lower()
        if konfirmasi == 'y' and os.path.exists(filepath):
            os.remove(filepath)
            print(f"✅ Berhasil menghapus {filepath}")
            changes_made.append(f"DELETE: {filepath}")

    return changes_made


def main(folder_path="."):
    print(f"=== 🛠️  AI SMART EDITOR (RAG ENABLED) ===\n📂 Workspace: {folder_path}")

    errors = validate_config()
    if errors:
        print("❌ Konfigurasi tidak lengkap:")
        for err in errors:
            print(f"   - {err}")
        return

    if not os.path.isdir(folder_path):
        print(f"❌ Folder tidak ditemukan: {folder_path}")
        return

    llm = get_llm(temperature=0.2)
    embeddings = get_embeddings()

    print("📥 Scanning dan indexing kodingan awal...")
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

        # ==========================================
        # 3-WAY CONTEXT ROUTING
        # ==========================================
        mentioned_files = find_mentioned_files(user_input, docs)

        if mentioned_files:
            # PRIORITAS 1: User menyebut file spesifik -> Inject FULL content
            print(f"🎯 File spesifik terdeteksi. Membaca isi file sepenuhnya...")
            context_parts = []
            for doc in mentioned_files:
                context_parts.append(f"// FULL FILE CONTENT: {doc['path']}\n{doc['content']}")
            
            context_str = "\n\n---\n\n".join(context_parts)
            prompt = f"BERIKUT ADALAH ISI FULL DARI FILE YANG DIMINTA:\n{context_str}\n\nINSTRUKSI USER: {user_input}"
            
        elif is_broad_query(user_input):
            # PRIORITAS 2: User bertanya umum -> Inject File Overview
            print("📋 Query umum terdeteksi — menggunakan file overview...")
            context_str = build_file_overview(folder_path, docs)
            prompt = f"DAFTAR LENGKAP FILE DI WORKSPACE (PREVIEW ONLY):\n{context_str}\n\nINSTRUKSI USER: {user_input}"
            
        else:
            # PRIORITAS 3: Query spesifik kode -> Gunakan RAG Semantic Search
            print("🔍 Mencari referensi kode yang relevan via RAG...")
            relevant_chunks = retriever.invoke(user_input)

            context_parts = []
            for doc in relevant_chunks:
                source = doc.metadata.get("source", "unknown")
                context_parts.append(f"// File Chunk: {source}\n{doc.page_content}")

            context_str = "\n\n---\n\n".join(context_parts)
            prompt = f"REFERENSI KODE RELEVAN:\n{context_str}\n\nINSTRUKSI USER: {user_input}"

        chat_history.append(HumanMessage(content=prompt))

        print("AI sedang menganalisis...")
        try:
            response = llm.invoke(chat_history)
            ai_text = response.content
            print(f"\nAI:\n{ai_text}\n")

            # Eksekusi operasi file
            perubahan = execute_file_operations(ai_text)
            
            # ==========================================
            # AUTO-REFRESH INDEX JIKA ADA PERUBAHAN
            # ==========================================
            if perubahan:
                print("\n🔄 Menyegarkan index otomatis agar AI mengingat perubahan terbaru...")
                docs, count = scan_workspace(folder_path)
                vectorstore = build_vectorstore(docs, embeddings)
                retriever = get_retriever(vectorstore, top_k=5)
                print(f"✅ Index berhasil diperbarui! ({count} file ter-index)")

            chat_history.append(AIMessage(content=ai_text))

        except Exception as e:
            print(f"❌ Terjadi kesalahan: {e}")
            # Hapus prompt terakhir dari history jika error agar tidak merusak flow
            chat_history.pop()


if __name__ == "__main__":
    main()