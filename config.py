"""
config.py — Konfigurasi terpusat untuk semua Agent.

Single source of truth: semua setting dibaca dari `.env` via python-dotenv.
"""

import os
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Environment Loading
# ---------------------------------------------------------------------------

load_dotenv(os.path.join(os.getcwd(), ".env"))

# ---------------------------------------------------------------------------
# Path
# ---------------------------------------------------------------------------

BASE_DIR: str = os.path.abspath(os.path.dirname(__file__))

# ---------------------------------------------------------------------------
# LLM Settings
# ---------------------------------------------------------------------------

LLM_API_KEY: str = os.getenv("ENOWXAI_KEY", "")
LLM_BASE_URL: str = os.getenv("ENOWXAI_URL", "")
LLM_MODEL: str = os.getenv("ENOWXAI_MODEL", "claude-opus-4.6")
LLM_TEMPERATURE: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
LLM_TIMEOUT: int = int(os.getenv("DEFAULT_TIMEOUT", "60"))
LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "4096"))

# ---------------------------------------------------------------------------
# Cloudflare R2 Settings
# ---------------------------------------------------------------------------

R2_ENDPOINT: str = os.getenv("R2_ENDPOINT", "")
R2_ACCESS_KEY: str = os.getenv("R2_ACCESS_KEY", "")
R2_SECRET_KEY: str = os.getenv("R2_SECRET_KEY", "")
R2_BUCKET_NAME: str = os.getenv("R2_BUCKET_NAME", "memory-ai-bagus")
R2_MEMORY_KEY: str = os.getenv("MEMORY_FILE", "chat_history.json")

# ---------------------------------------------------------------------------
# RAG Settings
# ---------------------------------------------------------------------------

CHUNK_SIZE: int = 1000
CHUNK_OVERLAP: int = 200
RETRIEVER_TOP_K: int = 4
EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

# ---------------------------------------------------------------------------
# Memory Settings
# ---------------------------------------------------------------------------

MAX_MEMORY_MESSAGES: int = 50

# ---------------------------------------------------------------------------
# System Prompts
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_BASIC: str = (
    "Kamu adalah asisten AI yang helpful dan menjawab dengan bahasa "
    "yang santai tapi informatif."
)

SYSTEM_PROMPT_MEMORY: str = (
    "Kamu adalah asisten asik yang selalu ingat nama user dan konteks "
    "percakapan sebelumnya."
)

SYSTEM_PROMPT_RAG: str = (
    "Kamu adalah AI Programmer Expert. Jawab pertanyaan user HANYA "
    "berdasarkan konteks kode yang diberikan. Jika konteks tidak cukup, "
    "katakan sejujurnya. Jangan mengarang kode."
)

SYSTEM_PROMPT_EDITOR: str = (
    "Kamu adalah Senior AI Programmer. Kamu bisa membaca, membuat, dan mengedit file.\n\n"
    "Setiap kali kamu memodifikasi, membuat, atau menulis ke dalam file, kamu WAJIB "
    "menggunakan format blok berikut secara persis:\n"
    "[SAVE: path_file_tujuan]\n"
    "Tuliskan seluruh isi file di sini...\n"
    "[/SAVE]\n\n"
    "ATURAN PENTING:\n"
    "1. Tag [SAVE: path] harus berada di barisnya sendiri.\n"
    "2. Tag penutup [/SAVE] WAJIB ada dan harus berada di baris baru paling akhir.\n"
    "3. Jangan gunakan backticks markdown (```) untuk membungkus blok SAVE ini."
)

# ---------------------------------------------------------------------------
# Proxy — bypass untuk localhost
# ---------------------------------------------------------------------------

os.environ.setdefault("no_proxy", "localhost,127.0.0.1")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_config() -> list[str]:
    """Validasi konfigurasi LLM minimum. Return list error (kosong = valid)."""
    errors = []
    if not LLM_API_KEY:
        errors.append("ENOWXAI_KEY belum diset di .env")
    if not LLM_BASE_URL:
        errors.append("ENOWXAI_URL belum diset di .env")
    return errors


def validate_r2_config() -> list[str]:
    """Validasi konfigurasi Cloudflare R2. Return list error (kosong = valid)."""
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


# ---------------------------------------------------------------------------
# Factory Functions
# ---------------------------------------------------------------------------

def get_llm(temperature: float | None = None, timeout: int | None = None):
    """Buat instance ChatOpenAI dengan konfigurasi dari .env."""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        model=LLM_MODEL,
        temperature=temperature if temperature is not None else LLM_TEMPERATURE,
        timeout=timeout if timeout is not None else LLM_TIMEOUT,
        max_tokens=LLM_MAX_TOKENS,
    )


def get_embeddings():
    """Buat instance HuggingFaceEmbeddings untuk semantic search."""
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
