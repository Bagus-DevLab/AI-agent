"""
agents/editor.py — Agent Editor dengan RAG + Persistent Memory.

Fitur:
  - Baca, buat, dan edit file via perintah natural language
  - RAG-based context retrieval untuk analisis kode
  - Persistent memory antar sesi
  - Security sandbox (file operations hanya di dalam workspace)
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


# ---------------------------------------------------------------------------
# Broad Query Detection
# ---------------------------------------------------------------------------

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
    """Deteksi apakah query bersifat umum/broad (bukan spesifik ke satu file)."""
    q = query.lower()
    if any(kw in q for kw in BROAD_EXPLICIT):
        return True
    has_subject = any(word in q for word in BROAD_SUBJECTS)
    has_action = any(word in q for word in BROAD_ACTIONS)
    return has_subject and has_action


# ---------------------------------------------------------------------------
# File Matching
# ---------------------------------------------------------------------------

def find_mentioned_files(query: str, docs: list) -> list:
    """Cari file yang disebutkan secara spesifik di query."""
    q = query.lower()
    return [doc for doc in docs if os.path.basename(doc["path"]).lower() in q]


def build_file_overview(folder_path: str, docs: list) -> str:
    """Bangun ringkasan semua file dengan preview 3 baris pertama."""
    lines = [
        f"Workspace: {os.path.abspath(folder_path)}",
        f"Total {len(docs)} file ter-index:\n",
    ]
    for doc in docs:
        preview = "\n".join(doc["content"].splitlines()[:3])
        truncated = f"{preview[:120]}..." if len(preview) > 120 else preview
        lines.append(f"  {doc['path']}\n  {truncated}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------

def is_safe_path(filepath: str) -> bool:
    """Pastikan filepath berada di dalam BASE_DIR (security sandbox)."""
    return _is_safe_path(filepath, BASE_DIR)


# ---------------------------------------------------------------------------
# File Operations — SAVE & DELETE parsing
# ---------------------------------------------------------------------------

def extract_save_blocks(ai_response: str) -> list[tuple[str, str]]:
    """
    Ekstrak blok [SAVE: path]...[/SAVE] dari response AI.

    Support dua format:
      1. [SAVE: path]\\n...\\n[/SAVE]
      2. [SAVE: path] ```lang ... ``` (legacy, nesting-aware)
    """
    results = []

    # Format 1: [SAVE: path]\n...\n[/SAVE]
    pattern = r'^\[SAVE:\s*(.+?)\]\n(.*?)\n^\[/SAVE\]'
    for match in re.finditer(pattern, ai_response, re.DOTALL | re.MULTILINE):
        filepath = match.group(1).strip()
        content = match.group(2)
        content = re.sub(r'^```\w*\n', '', content)
        content = re.sub(r'\n```$', '', content)
        results.append((filepath, content.strip()))

    # Format 2: legacy backtick format (fallback)
    if not results:
        results = _extract_legacy_save_blocks(ai_response)

    return results


def _extract_legacy_save_blocks(ai_response: str) -> list[tuple[str, str]]:
    """Parse format lama: [SAVE: path] ```lang ... ``` (nesting-aware)."""
    results = []
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


def execute_file_operations(ai_response: str) -> list[str]:
    """Eksekusi SAVE dan DELETE dari response AI, dengan konfirmasi user."""
    changes = []

    # SAVE operations
    for filepath, content in extract_save_blocks(ai_response):
        filepath = filepath.strip()
        if not is_safe_path(filepath):
            print(f"Ditolak: '{filepath}' di luar area project.")
            continue

        confirm = input(f"\nSimpan ke '{filepath}'? (y/n): ").strip().lower()
        if confirm == 'y':
            try:
                parent = os.path.dirname(os.path.abspath(filepath))
                if parent:
                    os.makedirs(parent, exist_ok=True)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"Berhasil update {filepath}")
                changes.append(f"SAVE: {filepath}")
            except Exception as e:
                print(f"Gagal simpan {filepath}: {e}")

    # DELETE operations
    for filepath in re.findall(r'^\[DELETE:\s*(.+?)\]', ai_response, re.MULTILINE):
        filepath = filepath.strip()
        if not is_safe_path(filepath):
            print(f"Ditolak: '{filepath}' di luar area project.")
            continue

        confirm = input(f"\nHapus '{filepath}'? (y/n): ").strip().lower()
        if confirm == 'y' and os.path.exists(filepath):
            os.remove(filepath)
            print(f"Berhasil hapus {filepath}")
            changes.append(f"DELETE: {filepath}")

    return changes


# ---------------------------------------------------------------------------
# Editor Memory — format konsisten "user"/"ai"
# ---------------------------------------------------------------------------

def load_editor_memory(path: str) -> list:
    """Load riwayat editor dari JSON. Return list of LangChain messages."""
    if not os.path.exists(path):
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            print("Format memori editor tidak valid, memulai baru.")
            return []

        messages = []
        for item in data:
            if not isinstance(item, dict):
                continue
            role = item.get("role", "")
            content = item.get("content", "")
            if not isinstance(content, str):
                content = str(content)
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "ai":
                messages.append(AIMessage(content=content))
        return messages

    except (json.JSONDecodeError, IOError, OSError) as e:
        print(f"Gagal load memori editor: {e}")
        return []


def save_editor_memory(chat_history: list, path: str) -> None:
    """Simpan riwayat editor ke JSON (hanya HumanMessage & AIMessage)."""
    data = []
    for msg in chat_history:
        if isinstance(msg, HumanMessage):
            data.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            data.append({"role": "ai", "content": msg.content})

    # Sliding window
    if len(data) > MAX_MEMORY_MESSAGES:
        data = data[-MAX_MEMORY_MESSAGES:]

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except (IOError, OSError) as e:
        print(f"Gagal simpan memori editor: {e}")


# ---------------------------------------------------------------------------
# Context Builder
# ---------------------------------------------------------------------------

def _build_prompt(user_input: str, docs: list, retriever, folder_path: str) -> str:
    """Tentukan konteks yang tepat berdasarkan jenis query, lalu bangun prompt."""
    mentioned = find_mentioned_files(user_input, docs)

    if mentioned:
        print("File spesifik terdeteksi, membaca isi penuh...")
        parts = [f"// FULL FILE: {d['path']}\n{d['content']}" for d in mentioned]
        return f"ISI LENGKAP FILE:\n{'---'.join(parts)}\n\nUSER: {user_input}"

    if is_broad_query(user_input):
        print("Query umum — menggunakan file overview...")
        overview = build_file_overview(folder_path, docs)
        return f"DAFTAR FILE WORKSPACE:\n{overview}\n\nUSER: {user_input}"

    print("Mencari referensi kode via RAG...")
    chunks = retriever.invoke(user_input)
    parts = [f"// {c.metadata.get('source', 'unknown')}\n{c.page_content}" for c in chunks]
    return f"REFERENSI KODE:\n{'---'.join(parts)}\n\nUSER: {user_input}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(folder_path: str = ".") -> None:
    global BASE_DIR
    BASE_DIR = os.path.abspath(folder_path)

    print(f"=== AI SMART EDITOR (RAG ENABLED) ===\nWorkspace: {BASE_DIR}")

    errors = validate_config()
    if errors:
        print("Konfigurasi tidak lengkap:")
        for err in errors:
            print(f"   - {err}")
        return

    if not os.path.isdir(folder_path):
        print(f"Folder tidak ditemukan: {folder_path}")
        return

    llm = get_llm(temperature=0.2)
    embeddings = get_embeddings()

    # Scan & build index
    print("Scanning dan indexing kodingan...")
    docs, count = scan_workspace(folder_path)
    if not docs:
        print("Tidak ada file kodingan yang ditemukan.")
        return

    vectorstore = build_vectorstore(docs, embeddings)
    retriever = get_retriever(vectorstore, top_k=5)

    # Load memory
    memori_path = f"editor_{os.path.basename(BASE_DIR)}.json"
    past_messages = load_editor_memory(memori_path)

    chat_history = [SystemMessage(content=SYSTEM_PROMPT_EDITOR)]
    chat_history.extend(past_messages)

    if past_messages:
        print(f"Memuat {len(past_messages)} pesan dari ingatan sebelumnya.")

    print(f"{count} file berhasil di-index. Siap menerima perintah.")
    print("Ketik 'exit' untuk keluar, 'clear' untuk hapus memori.\n")

    while True:
        try:
            user_input = input("\nLu: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            break

        if user_input.lower() in ("exit", "quit"):
            print("Bye!")
            break

        if user_input.lower() == "clear":
            chat_history = [SystemMessage(content=SYSTEM_PROMPT_EDITOR)]
            save_editor_memory(chat_history, memori_path)
            print("Memori editor dihapus.\n")
            continue

        if not user_input:
            continue

        prompt = _build_prompt(user_input, docs, retriever, folder_path)
        chat_history.append(HumanMessage(content=prompt))
        print("AI sedang menganalisis...")

        try:
            response = llm.invoke(chat_history)
            ai_text = response.content
            print(f"\nAI:\n{ai_text}\n")

            chat_history.append(AIMessage(content=ai_text))
            save_editor_memory(chat_history, memori_path)

            # Eksekusi file operations & refresh index jika ada perubahan
            if execute_file_operations(ai_text):
                print("\nMenyegarkan index...")
                docs, count = scan_workspace(folder_path)
                vectorstore = build_vectorstore(docs, embeddings)
                retriever = get_retriever(vectorstore, top_k=5)
                print(f"Index diperbarui! ({count} file)")

        except Exception as e:
            print(f"Terjadi kesalahan: {e}")
            if chat_history and isinstance(chat_history[-1], HumanMessage):
                chat_history.pop()


if __name__ == "__main__":
    main()
