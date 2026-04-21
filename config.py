"""
config.py — Konfigurasi terpusat untuk semua agent.
Semua setting LLM, embedding, dan prompt ada di sini.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# === LLM Settings ===
LLM_API_KEY = os.getenv("ENOWXAI_KEY", "")
LLM_BASE_URL = os.getenv("ENOWXAI_URL", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "120"))

# === Cloudflare R2 Settings ===
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

# === System Prompts ===
SYSTEM_PROMPT_BASIC = "Kamu adalah asisten AI yang helpful dan menjawab dengan bahasa yang santai tapi informatif."
SYSTEM_PROMPT_MEMORY = "Kamu adalah asisten asik yang selalu ingat nama user dan konteks percakapan sebelumnya."
SYSTEM_PROMPT_RAG = (
    "Kamu adalah AI Programmer Expert. Jawab pertanyaan user HANYA berdasarkan konteks kode yang diberikan. "
    "Jika konteks tidak cukup, bilang terus terang. Jangan mengarang."
)
SYSTEM_PROMPT_EDITOR = (
    "Kamu adalah Senior AI Programmer. Kamu bisa membaca, membuat, dan mengedit file. "
    "Selalu berikan kode yang lengkap dan bisa langsung dijalankan."
)

# === Bypass Proxy (untuk WSL/Docker) ===
os.environ["no_proxy"] = "*"


def validate_config():
    """Validasi konfigurasi minimum yang dibutuhkan."""
    errors = []
    if not LLM_API_KEY:
        errors.append("ENOWXAI_KEY belum diset di .env")
    if not LLM_BASE_URL:
        errors.append("ENOWXAI_URL belum diset di .env")
    if errors:
        print("⚠️  KONFIGURASI TIDAK LENGKAP:")
        for err in errors:
            print(f"   ❌ {err}")
        print(f"\n💡 Buat file .env di root project dengan isi:")
        print(f"   ENOWXAI_KEY=your_api_key_here")
        print(f"   ENOWXAI_URL=https://your-llm-endpoint.com/v1")
        return False
    return True


def validate_r2_config():
    """Validasi konfigurasi R2 untuk cloud agent."""
    errors = []
    if not R2_ACCOUNT_ID:
        errors.append("R2_ACCOUNT_ID belum diset")
    if not R2_ACCESS_KEY:
        errors.append("R2_ACCESS_KEY belum diset")
    if not R2_SECRET_KEY:
        errors.append("R2_SECRET_KEY belum diset")
    if errors:
        print("⚠️  KONFIGURASI R2 TIDAK LENGKAP:")
        for err in errors:
            print(f"   ❌ {err}")
        return False
    return True


def get_llm(temperature=None, timeout=None):
    """Factory function untuk membuat instance LLM yang konsisten."""
    if not validate_config():
        raise RuntimeError("Konfigurasi LLM tidak valid. Cek file .env")

    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        model=LLM_MODEL,
        temperature=temperature if temperature is not None else LLM_TEMPERATURE,
        timeout=timeout if timeout is not None else LLM_TIMEOUT,
    )


def get_embeddings():
    """Factory function untuk membuat instance Embeddings yang konsisten."""
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
