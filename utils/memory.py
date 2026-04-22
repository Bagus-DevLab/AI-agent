"""
utils/memory.py — Load dan simpan memori percakapan lokal.
"""

import os
import json
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from config import MAX_MEMORY_MESSAGES


def load_memori_lokal(system_prompt: str, path: str = "chat_memory.json") -> list:
    """
    Load memori percakapan dari file JSON lokal.

    Returns:
        List of LangChain messages, dimulai dengan SystemMessage.
    """
    history = [SystemMessage(content=system_prompt)]

    if not os.path.exists(path):
        return history

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            print(f"Format memori tidak valid di {path}, memulai baru.")
            return history

        for item in data:
            if not isinstance(item, dict):
                continue
            if "role" not in item or "content" not in item:
                continue
            if item["role"] == "user":
                history.append(HumanMessage(content=item["content"]))
            elif item["role"] == "ai":
                history.append(AIMessage(content=item["content"]))

    except json.JSONDecodeError as e:
        print(f"File memori corrupt ({path}): {e}")
    except (IOError, OSError) as e:
        print(f"Gagal membaca file memori ({path}): {e}")

    return history


def simpan_memori_lokal(history: list, path: str = "chat_memory.json") -> None:
    """
    Simpan memori percakapan ke file JSON lokal.
    Hanya simpan HumanMessage dan AIMessage, dengan sliding window.
    """
    data = []
    for m in history:
        if isinstance(m, HumanMessage):
            data.append({"role": "user", "content": m.content})
        elif isinstance(m, AIMessage):
            data.append({"role": "ai", "content": m.content})

    if len(data) > MAX_MEMORY_MESSAGES:
        data = data[-MAX_MEMORY_MESSAGES:]

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except (IOError, OSError) as e:
        print(f"Gagal menyimpan memori ke {path}: {e}")


def trim_history(history: list, max_messages: int | None = None) -> list:
    """
    Trim history untuk menghindari token limit LLM.
    Pertahankan SystemMessage di awal + N pesan terakhir.
    """
    limit = max_messages or MAX_MEMORY_MESSAGES

    system_msgs = [m for m in history if isinstance(m, SystemMessage)]
    chat_msgs = [m for m in history if not isinstance(m, SystemMessage)]

    if len(chat_msgs) > limit:
        chat_msgs = chat_msgs[-limit:]

    return system_msgs + chat_msgs
