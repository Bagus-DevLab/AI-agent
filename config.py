"""
config.py — Konfigurasi terpusat.
Menambahkan proteksi agar .env wajib terbaca.
"""

import os
from dotenv import load_dotenv

# Paksa load .env dari direktori saat ini
load_dotenv(os.path.join(os.getcwd(), '.env'))

# === LLM Settings ===
LLM_API_KEY = os.getenv("ENOWXAI_KEY", "")
LLM_BASE_URL = os.getenv("ENOWXAI_URL", "")

# JANGAN beri gpt-4o-mini sebagai default jika kamu hanya pakai Claude
LLM_MODEL = os.getenv("LLM_MODEL", "claude-opus-4.6") 
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "300")) # Diperbesar ke 300s

# === RAG Settings ===
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
RETRIEVER_TOP_K = 4
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# === System Prompts ===
SYSTEM_PROMPT_BASIC = "Kamu adalah asisten AI yang helpful dan menjawab dengan bahasa yang santai tapi informatif."
SYSTEM_PROMPT_MEMORY = "Kamu adalah asisten asik yang selalu ingat nama user dan konteks percakapan sebelumnya."
SYSTEM_PROMPT_RAG = (
    "Kamu adalah AI Programmer Expert. Jawab pertanyaan user HANYA berdasarkan konteks kode yang diberikan. "
    "Jangan mengarang informasi di luar konteks."
)
SYSTEM_PROMPT_EDITOR = (
    "Kamu adalah Senior AI Programmer. Kamu bisa membaca, membuat, dan mengedit file. "
    "Gunakan format [SAVE: path], [DELETE: path], atau [MOVE: path] untuk modifikasi file."
)

os.environ["no_proxy"] = "*"

def get_llm(temperature=None, timeout=None):
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        model=LLM_MODEL,
        temperature=temperature if temperature is not None else LLM_TEMPERATURE,
        timeout=timeout if timeout is not None else LLM_TIMEOUT,
    )

def get_embeddings():
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)