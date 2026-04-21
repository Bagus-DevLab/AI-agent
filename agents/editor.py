"""
editor.py — Agent dengan kemampuan membaca dan mengedit file.
Pengganti agent_edit.py yang sudah di-refactor.

Usage: python -m agents.editor [folder_path]
"""

import os
import sys
import re
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from config import get_llm, get_embeddings, SYSTEM_PROMPT_EDITOR
from utils.scanner import scan_workspace, get_file_list
from utils.vectorstore import build_vectorstore, get_retriever


def execute_file_operations(ai_response):
    """
    Parse dan eksekusi operasi file dari respons AI.
    Mendukung: [SAVE], [DELETE], [MOVE]
    
    Returns:
        list: Daftar operasi yang berhasil dieksekusi
    """
    operations = []

    # Pattern: [SAVE: path/file.ext]
    save_pattern = r'\[SAVE:\s*(.+?)\]\s*