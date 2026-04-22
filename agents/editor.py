"""
agents/editor.py — Agent Editor dengan RAG + Persistent Memory.
Memory system menggunakan format konsisten "user"/"ai" agar kompatibel
dengan utils/memory.py dan tidak ada mismatch role format.
"""

import os
import re
import json
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from config import get_llm, get_embeddings, SYSTEM_PROMPT_EDITOR, validate_config, MAX_MEMORY_MESSAGES
from utils.scanner import scan_workspace, get_file_list
from utils.vectorstore import build_vectorstore, get_retriever
from utils.security import is_safe_path as _is_safe_path

# Base directory — di-update dinamis di main()
BASE_DIR = os.path.abspath(os.getcwd())

# ==========================================
# BROAD QUERY DETECTION
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
    """Deteksi apakah query bersifat umum/broad menggunakan dua lapis filter."""
    query_lower = query.lower()
    if any(kw in query_lower for kw in BROAD_EXPLICIT):
        return True
    has_subject = any(word in query_lower for word in BROAD_SUBJECTS)
    has_action = any(word in query_lower for word in BROAD_ACTIONS)
    return has_subject and has_action


def find_mentioned_files(query: str, docs: list) -> list:
    """Mencari file yang disebutkan secara spesifik di query."""
    mentioned = []
    query_lower = query.lower()
    for doc in docs:
        filename = os.path.basename(doc["path"]).lower()
        if filename in query_lower:
            mentioned.append(doc)
    return mentioned


def build_file_overview(folder_path: str, docs: list) -> str:
    """Bangun ringkasan semua file dengan preview 3 baris."""
    lines = [
        f"📂 Workspace: {os.path.abspath(folder_path)}",
        f"Total {len(docs)} file ter-index:\n"
    ]
    for doc in docs:
        preview = "\n".join(doc["content"].splitlines()[:3])
        lines.append(f"• {doc['path']}\n  {preview[:120]}{'...' if len(preview) > 120 else ''}")
    return "\n".join(lines)


# ==========================================
# SECURITY
# ==========================================
def is_safe_path(filepath: str) -> bool:
    """Pastikan filepath berada di dalam BASE_DIR (security sandbox)."""
    return _is_safe_path(filepath, BASE_DIR)


# ==========================================
# FILE OPERATIONS
# ==========================================
def extract_save_blocks(ai_response: str):
    """
    Nesting-aware parser untuk ekstrak blok [SAVE: path]...[/SAVE].
    Support dua format:
      1. [SAVE: path] ... [/SAVE]  (format baru dari SYSTEM_PROMPT_EDITOR)
      2. [SAVE: path] ```lang ... ``` (format lama dengan backtick)
    """
    results = []

    # Format 1: [SAVE: path]\n...\n[/SAVE]
    pattern_new = r'^\[SAVE:\s*(.+?)\]\n(.*?)\n^\[/SAVE\]'
    for match in re.finditer(pattern_new, ai_response, re.DOTALL | re.MULTILINE):
        filepath = match.group(1).strip()
        content = match.group(2)
        # Strip optional backtick wrapper jika ada
        content = re.sub(r'^```\w*\n', '', content)
        content = re.sub(r'\n```$', '', content)
        results.append((filepath, content.strip()))

    # Format 2: [SAVE: path] ```lang ... ``` (nesting-aware)
    if not results:
        save_tags = list(re.finditer(r'\[SAVE:\s*(.+?)\]', ai_response))
        for tag in save_tags:
            filepath = tag.group(1).strip()
            after_tag = ai_response[tag.end():]
            open_match = re.match(r'\s*```(\w*)\n', after_tag)
            if not open_match:
                continue
            content_after = after_tag[open_match.end():]
            lines = content_after.split('\n')
            depth = 1
            content_lines = []
            for line in lines:
                if re.match(r'^```\w+', line):
                    depth += 1
                    content_lines.append(line)
                elif re.match(r'^```\s*$', line):
                    depth -= 1
                    if depth == 0:
                        break
                    content_lines.append(line)
                else:
                    content_lines.append(line)
            results.append((filepath, '\n'.join(content_lines)))

    return results


def execute_file_operations(ai_response: str) -> list:
    """Eksekusi SAVE dan DELETE dengan konfirmasi user."""
    changes_made = []

    # SAVE
    for filepath, file_content in extract_save_blocks(ai_response):
        filepath = filepath.strip()
        if not is_safe_path(filepath):
            print(f"🚫 Ditolak: '{filepath}' di luar area project.")
            continue
        konfirmasi = input(f"\n💾 Simpan ke '{filepath}'? (y/n): ").strip().lower()
        if konfirmasi == 'y':
            try:
                parent_dir = os.path.dirname(os.path.abspath(filepath))
                if parent_dir:
                    os.makedirs(parent_dir, exist_ok=True)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(file_content)
                print(f"✅ Berhasil update {filepath}")
                changes_made.append(f"SAVE: {filepath}")
            except Exception as e:
                print(f"❌ Gagal simpan {filepath}: {e}")

    # DELETE
    for filepath in re.findall(r'^\[DELETE:\s*(.+?)\]', ai_response, re.MULTILINE):
        filepath = filepath.strip()
        if not is_safe_path(filepath):
            print(f"🚫 Ditolak: '{filepath}' di luar area project.")
            continue
        konfirmasi = input(f"\n🗑️  Hapus '{filepath}'? (y/n): ").strip().lower()
        if konfirmasi == 'y' and os.path.exists(filepath):
            os.remove(filepath)
            print(f"✅ Berhasil hapus {filepath}")
            changes_made.append(f"DELETE: {filepath}")

    return changes_made


# ==========================================
# MEMORY SYSTEM — KONSISTEN "user"/"ai"
# ==========================================
def load_editor_memory(path: str) -> list:
    """
    Load riwayat editor dari JSON.
    Format: [{"role": "user", "content": "..."}, {"role": "ai", "content": "..."}]
    Return: List of LangChain messages (HumanMessage / AIMessage)
    """
    if not os.path.exists(path):
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            print(f"⚠️ Format memori editor tidak valid, memulai baru.")
            return []

        messages = []
        for item in data:
            if not isinstance(item, dict):
                continue
            role = item.get("role", "")
            content = item.get("content", "")
            if not isinstance(content, str):
                content = str(content)
            # Format konsisten: "user" → HumanMessage, "ai" → AIMessage
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "ai":
                messages.append(AIMessage(content=content))
            # Skip role lain (system, human, dll) — tidak diproses

        return messages

    except (json.JSONDecodeError, IOError, OSError) as e:
        print(f"⚠️ Gagal load memori editor: {e}")
        return []


def save_editor_memory(chat_history: list, path: str):
    """
    Simpan riwayat editor ke JSON.
    Hanya simpan HumanMessage dan AIMessage (skip SystemMessage).
    Format: [{"role": "user"/"ai", "content": "..."}]
    """
    data = []
    for msg in chat_history:
        if isinstance(msg, HumanMessage):
            data.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            data.append({"role": "ai", "content": msg.content})
        # Skip SystemMessage — tidak perlu disimpan

    # Sliding window
    if len(data) > MAX_MEMORY_MESSAGES:
        data = data[-MAX_MEMORY_MESSAGES:]

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except (IOError, OSError) as e:
        print(f"⚠️ Gagal simpan memori editor: {e}")


# ==========================================
# MAIN
# ==========================================
def main(folder_path="."):
    global BASE_DIR
    BASE_DIR = os.path.abspath(folder_path)

    print(f"=== 🛠️  AI SMART EDITOR (RAG ENABLED) ===\n📂 Workspace: {BASE_DIR}")

    # Validasi config
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

    # Scan & build index
    print("📥 Scanning dan indexing kodingan...")
    docs, count = scan_workspace(folder_path)
    if not docs:
        print("❌ Tidak ada file kodingan yang ditemukan.")
        return

    vectorstore = build_vectorstore(docs, embeddings)
    retriever = get_retriever(vectorstore, top_k=5)

    # Load memori editor — format konsisten user/ai
    memori_path = f"editor_{os.path.basename(BASE_DIR)}.json"
    past_messages = load_editor_memory(memori_path)

    # Bangun chat_history: SystemMessage + history lama
    chat_history = [SystemMessage(content=SYSTEM_PROMPT_EDITOR)]
    chat_history.extend(past_messages)

    if past_messages:
        print(f"🧠 Memuat {len(past_messages)} pesan dari ingatan sebelumnya.")

    print(f"✅ {count} file berhasil di-index. Siap menerima perintah.")
    print("Ketik 'exit' untuk keluar, 'clear' untuk hapus memori.\n")

    while True:
        try:
            user_input = input("\nLu: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Bye!")
            break

        if user_input.lower() in ["exit", "quit"]:
            print("👋 Bye!")
            break
        if user_input.lower() == "clear":
            chat_history = [SystemMessage(content=SYSTEM_PROMPT_EDITOR)]
            save_editor_memory(chat_history, memori_path)
            print("🗑️ Memori editor dihapus.\n")
            continue
        if not user_input:
            continue

        # Tentukan konteks
        mentioned_files = find_mentioned_files(user_input, docs)
        if mentioned_files:
            print(f"🎯 File spesifik terdeteksi, membaca isi penuh...")
            context_parts = [
                f"// FULL FILE: {doc['path']}\n{doc['content']}"
                for doc in mentioned_files
            ]
            prompt = f"ISI LENGKAP FILE:\n{'---'.join(context_parts)}\n\nUSER: {user_input}"
        elif is_broad_query(user_input):
            print("📋 Query umum — menggunakan file overview...")
            prompt = f"DAFTAR FILE WORKSPACE:\n{build_file_overview(folder_path, docs)}\n\nUSER: {user_input}"
        else:
            print("🔍 Mencari referensi kode via RAG...")
            relevant_chunks = retriever.invoke(user_input)
            context_parts = [
                f"// {doc.metadata.get('source', 'unknown')}\n{doc.page_content}"
                for doc in relevant_chunks
            ]
            prompt = f"REFERENSI KODE:\n{'---'.join(context_parts)}\n\nUSER: {user_input}"

        chat_history.append(HumanMessage(content=prompt))
        print("🤖 AI sedang menganalisis...")

        try:
            response = llm.invoke(chat_history)
            ai_text = response.content
            print(f"\nAI:\n{ai_text}\n")

            chat_history.append(AIMessage(content=ai_text))

            # Simpan memori setiap setelah reply
            save_editor_memory(chat_history, memori_path)

            # Eksekusi file operations jika ada
            if execute_file_operations(ai_text):
                print("\n🔄 Menyegarkan index...")
                docs, count = scan_workspace(folder_path)
                vectorstore = build_vectorstore(docs, embeddings)
                retriever = get_retriever(vectorstore, top_k=5)
                print(f"✅ Index diperbarui! ({count} file)")

        except Exception as e:
            print(f"❌ Terjadi kesalahan: {e}")
            # Pop HumanMessage terakhir agar history tidak corrupt
            if chat_history and isinstance(chat_history[-1], HumanMessage):
                chat_history.pop()


if __name__ == "__main__":
    main()