"""
config.py — Konfigurasi terpusat untuk semua agent.
"""

import os
from dotenv import load_dotenv

# Paksa load .env dari direktori kerja saat ini
load_dotenv(os.path.join(os.getcwd(), '.env'))

# === LLM Settings ===
LLM_API_KEY = os.getenv("ENOWXAI_KEY", "")
LLM_BASE_URL = os.getenv("ENOWXAI_URL", "")
# Gunakan model default yang valid
LLM_MODEL = os.getenv("ENOWXAI_MODEL", "claude-sonnet-4-20250514")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "300"))

# === Cloudflare R2 Settings ===
R2_ENDPOINT = os.getenv("R2_ENDPOINT", "")
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY", "")
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY", "")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "ai-memory")
R2_MEMORY_KEY = os.getenv("R2_MEMORY_KEY", "chat_memory.json")

# === RAG Settings ===
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
RETRIEVER_TOP_K = 4
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# === Memory Settings ===
MAX_MEMORY_MESSAGES = 50  # Batas maksimal pesan dalam memori

# === System Prompts ===
SYSTEM_PROMPT_BASIC = "Kamu adalah asisten AI yang helpful dan menjawab dengan bahasa yang santai tapi informatif."
SYSTEM_PROMPT_MEMORY = "Kamu adalah asisten asik yang selalu ingat nama user dan konteks percakapan sebelumnya."
SYSTEM_PROMPT_RAG = (
    "Kamu adalah AI Programmer Expert. Jawab pertanyaan user HANYA berdasarkan konteks kode yang diberikan. "
    "Jika konteks tidak cukup, katakan sejujurnya. Jangan mengarang kode."
)
SYSTEM_PROMPT_EDITOR = (
    "Kamu adalah Senior AI Programmer. Kamu bisa membaca, membuat, dan mengedit file. "
    "Gunakan tag [SAVE: path] untuk setiap modifikasi file."
)

# Bypass proxy hanya untuk localhost, bukan semua koneksi
os.environ.setdefault("no_proxy", "localhost,127.0.0.1")


def validate_config():
    """Validasi konfigurasi minimum yang dibutuhkan."""
    errors = []
    if not LLM_API_KEY:
        errors.append("ENOWXAI_KEY belum diset di .env")
    if not LLM_BASE_URL:
        errors.append("ENOWXAI_URL belum diset di .env")
    return errors


def validate_r2_config():
    """Validasi konfigurasi R2 untuk cloud agent."""
    errors = []
    if not R2_ENDPOINT:
        errors.append("R2_ENDPOINT belum diset di .env")
    if not R2_ACCESS_KEY:
        errors.append("R2_ACCESS_KEY belum diset di .env")
    if not R2_SECRET_KEY:
        errors.append("R2_SECRET_KEY belum diset di .env")
    if not R2_BUCKET_NAME:
        errors.append("R2_BUCKET_NAME belum diset di .env")
    return errors


def get_llm(temperature=None, timeout=None):
    """Factory function untuk LLM."""
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        model=LLM_MODEL,
        temperature=temperature if temperature is not None else LLM_TEMPERATURE,
        timeout=timeout if timeout is not None else LLM_TIMEOUT,
    )


def get_embeddings():
    """Factory function untuk Embeddings."""
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
