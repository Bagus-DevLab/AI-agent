"""
agents/editor.py — Agent dengan kemampuan membaca, menulis, dan mengelola file.
Mendukung operasi otomatis via tag [SAVE], [DELETE], dan [MOVE] dengan konfirmasi user.
"""

import os
import re
import shutil
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from config import get_llm, SYSTEM_PROMPT_EDITOR, validate_config
from utils.scanner import scan_workspace


def execute_file_operations(ai_response):
    """
    Mencari dan mengeksekusi perintah manipulasi file dari jawaban AI dengan konfirmasi manual.
    Format yang didukung: [SAVE: path], [DELETE: path], [MOVE: old -> new]
    
    Returns:
        List of string describing changes made
    """
    changes_made = []

    # 1. Logika SAVE (Simpan/Update File)
    # Mendukung: [SAVE: path] diikuti code block (