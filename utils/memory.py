"""
utils/memory.py — Helper untuk menyimpan dan memuat chat memory.
Mendukung penyimpanan lokal (JSON) dan cloud (R2).
"""

import os
import json
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

MEMORY_FILE = "chat_memory.json"


def load_memori_lokal(system_prompt: str, filepath: str = MEMORY_FILE) -> list:
    """
    Load chat history dari file JSON lokal.
    Selalu return list dengan SystemMessage di index 0.
    """
    chat_history = [SystemMessage(content=system_prompt)]

    if not os.path.exists(filepath):
        return chat_history

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                print("⚠️  File memory kosong, mulai fresh.")
                return chat_history
            data = json.loads(content)

        if not isinstance(data, list):
            print("⚠️  Format memory tidak valid, mulai fresh.")
            return chat_history

        for msg in data:
            if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                continue
            if msg["role"] == "user":
                chat_history.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                chat_history.append(AIMessage(content=msg["content"]))

    except json.JSONDecodeError:
        print(f"⚠️  File {filepath} corrupt (bukan JSON valid). Mulai fresh.")
        # Backup file corrupt
        backup_path = filepath + ".corrupt"
        try:
            os.rename(filepath, backup_path)
            print(f"   📦 File lama di-backup ke {backup_path}")
        except OSError:
            pass
    except Exception as e:
        print(f"⚠️  Gagal load memory: {e}. Mulai fresh.")

    return chat_history


def simpan_memori_lokal(chat_history: list, filepath: str = MEMORY_FILE):
    """
    Simpan chat history ke file JSON lokal.
    Skip SystemMessage, hanya simpan Human dan AI messages.
    """
    data = []
    for msg in chat_history:
        if isinstance(msg, HumanMessage):
            data.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            data.append({"role": "assistant", "content": msg.content})

    try:
        # Tulis ke temp file dulu, lalu rename (atomic write)
        temp_path = filepath + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(temp_path, filepath)
    except Exception as e:
        print(f"⚠️  Gagal simpan memory: {e}")
