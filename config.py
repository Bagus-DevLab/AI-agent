"""
config.py — Shared Configuration untuk seluruh Agent
Semua setting terpusat di sini, tidak ada lagi hardcode di masing-masing file.
"""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# === LLM Settings ===
LLM_API_KEY = os.getenv("ENOWXAI_KEY", "")
LLM_BASE_URL = os.getenv("ENOWXAI_URL", "")
LLM_MODEL = os.getenv("ENOWXAI_MODEL", "claude-opus-4.6")
LLM_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
LLM_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "60"))

# === Cloudflare R2 Settings ===
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY", "")
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY", "")
R2_ENDPOINT = os.getenv("R2_ENDPOINT", "")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "ai-memory")

# === File & Path Settings ===
MEMORY_FILE = os.getenv("MEMORY_FILE", "chat_history.json")
CLOUD_FILE_NAME = "chat_history.json"

# === Scanner Settings ===
FORBIDDEN_DIRS = {
    "venv", ".venv", "env", ".git", "node_modules",
    "__pycache__", ".cache", "build", "dist",
    ".idea", ".vscode", "faiss_index"
}

ALLOWED_EXTS = {
    ".py", ".go", ".js", ".ts", ".jsx", ".tsx",
    ".html", ".css", ".md", ".txt", ".sh", ".php",
    ".yaml", ".yml", ".toml", ".json", ".sql",
    ".rs", ".java", ".c", ".cpp", ".h", ".rb"
}

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


def get_llm(temperature=None, timeout=None):
    """Factory function untuk membuat instance LLM yang konsisten."""
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


def get_r2_client():
    """Factory function untuk membuat S3-compatible client ke Cloudflare R2."""
    import boto3
    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
    )
