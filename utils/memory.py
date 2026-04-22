"""
utils/memory.py — Helper untuk load dan simpan memori percakapan lokal.
"""

import os
import json
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from config import MAX_MEMORY_MESSAGES


def load_memori_lokal(system_prompt, path="chat_memory.json"):
    """
    Load memori percakapan dari file JSON lokal.
    
    Args:
        system_prompt: System prompt untuk AI
        path: Path ke file memori JSON
    
    Returns:
        List of LangChain messages
    """
    history = [SystemMessage(content=system_prompt)]

    if not os.path.exists(path):
        return history

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            print(f"⚠️ Format memori tidak valid di {path}, memulai baru.")
            return history

        for item in data:
            # Validasi struktur setiap item
            if not isinstance(item, dict):
                continue
            if "role" not in item or "content" not in item:
                continue

            if item["role"] == "user":
                history.append(HumanMessage(content=item["content"]))
            elif item["role"] == "ai":
                history.append(AIMessage(content=item["content"]))

    except json.JSONDecodeError as e:
        print(f"⚠️ File memori corrupt ({path}): {e}")
        print("   Memulai percakapan baru.")
    except (IOError, OSError) as e:
        print(f"⚠️ Gagal membaca file memori ({path}): {e}")

    return history


def simpan_memori_lokal(history, path="chat_memory.json"):
    """
    Simpan memori percakapan ke file JSON lokal.
    Menerapkan sliding window untuk membatasi ukuran memori.
    
    Args:
        history: List of LangChain messages
        path: Path ke file memori JSON
    """
    # Filter hanya pesan user dan AI (skip SystemMessage dan tipe lain)
    data = []
    for m in history:
        if isinstance(m, HumanMessage):
            data.append({"role": "user", "content": m.content})
        elif isinstance(m, AIMessage):
            data.append({"role": "ai", "content": m.content})
        # Skip SystemMessage dan tipe lain (ToolMessage, FunctionMessage, dll.)

    # Terapkan sliding window — simpan hanya N pesan terakhir
    if len(data) > MAX_MEMORY_MESSAGES:
        data = data[-MAX_MEMORY_MESSAGES:]

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except (IOError, OSError) as e:
        print(f"⚠️ Gagal menyimpan memori ke {path}: {e}")


def trim_history(history, max_messages=None):
    """
    Trim history untuk menghindari token limit LLM.
    Mempertahankan SystemMessage di awal + N pesan terakhir.
    
    Args:
        history: List of LangChain messages
        max_messages: Batas jumlah pesan (default dari config)
    
    Returns:
        Trimmed history
    """
    limit = max_messages if max_messages else MAX_MEMORY_MESSAGES

    # Pisahkan system message dari percakapan
    system_msgs = [m for m in history if isinstance(m, SystemMessage)]
    chat_msgs = [m for m in history if not isinstance(m, SystemMessage)]

    # Trim jika melebihi batas
    if len(chat_msgs) > limit:
        chat_msgs = chat_msgs[-limit:]

    return system_msgs + chat_msgs
