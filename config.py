"""
config.py — Konfigurasi Terpusat untuk Semua Agent
====================================================

File ini bertanggung jawab sebagai **single source of truth** untuk seluruh
konfigurasi aplikasi AI Code Assistant. Semua setting dibaca dari file `.env`
di root project menggunakan `python-dotenv`.

Modul ini menyediakan:
    - Konfigurasi koneksi LLM (API key, base URL, model, dll.)
    - Konfigurasi Cloudflare R2 untuk penyimpanan memori cloud
    - Parameter RAG (chunk size, overlap, top-k retrieval)
    - Batas memori percakapan
    - System prompt untuk setiap jenis agent
    - Factory function untuk inisialisasi LLM dan Embeddings
    - Fungsi validasi konfigurasi

Penggunaan:
    >>> from config import get_llm, get_embeddings, validate_config
    >>> errors = validate_config()
    >>> if not errors:
    ...     llm = get_llm()
    ...     embeddings = get_embeddings()

Catatan:
    - File `.env` WAJIB ada di root project sebelum menjalankan agent manapun.
    - File ini secara otomatis di-skip oleh scanner agar API key tidak ter-index.
"""

import os
from dotenv import load_dotenv

# ============================================================================
# 🔧 ENVIRONMENT LOADING
# ============================================================================
# Paksa load .env dari direktori kerja saat ini (bukan dari lokasi file ini).
# Ini memastikan .env selalu terbaca meskipun script dijalankan dari subfolder.

load_dotenv(os.path.join(os.getcwd(), ".env"))

# ============================================================================
# 📁 PATH CONFIGURATION
# ============================================================================
# Base directory dihitung dari lokasi file config.py ini berada.
# Digunakan sebagai referensi path relatif di seluruh aplikasi.

BASE_DIR: str = os.path.abspath(os.path.dirname(__file__))

# ============================================================================
# 🤖 LLM (Large Language Model) SETTINGS
# ============================================================================
# Konfigurasi koneksi ke LLM API.
#
# Variabel .env yang dibaca:
#   - ENOWXAI_KEY       : API key untuk autentikasi
#   - ENOWXAI_URL       : Base URL endpoint API (OpenAI-compatible)
#   - ENOWXAI_MODEL     : Nama model yang digunakan
#   - DEFAULT_TEMPERATURE: Tingkat kreativitas output (0.0 = deterministik, 1.0 = kreatif)
#   - DEFAULT_TIMEOUT    : Batas waktu request dalam detik

LLM_API_KEY: str = os.getenv("ENOWXAI_KEY", "")
LLM_BASE_URL: str = os.getenv("ENOWXAI_URL", "")
LLM_MODEL: str = os.getenv("ENOWXAI_MODEL", "claude-opus-4.6")
LLM_TEMPERATURE: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
LLM_TIMEOUT: int = int(os.getenv("DEFAULT_TIMEOUT", "60"))
LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "4096"))

# ============================================================================
# ☁️ CLOUDFLARE R2 SETTINGS
# ============================================================================
# Konfigurasi Cloudflare R2 Object Storage untuk penyimpanan memori
# percakapan secara persisten di cloud.
#
# Variabel .env yang dibaca:
#   - R2_ENDPOINT   : URL endpoint S3-compatible dari Cloudflare R2
#   - R2_ACCESS_KEY : Access key ID untuk autentikasi
#   - R2_SECRET_KEY : Secret access key untuk autentikasi
#   - R2_BUCKET_NAME: Nama bucket R2 yang digunakan
#   - MEMORY_FILE   : Nama file JSON untuk menyimpan riwayat chat

R2_ENDPOINT: str = os.getenv("R2_ENDPOINT", "")
R2_ACCESS_KEY: str = os.getenv("R2_ACCESS_KEY", "")
R2_SECRET_KEY: str = os.getenv("R2_SECRET_KEY", "")
R2_BUCKET_NAME: str = os.getenv("R2_BUCKET_NAME", "memory-ai-bagus")
R2_MEMORY_KEY: str = os.getenv("MEMORY_FILE", "chat_history.json")

# ============================================================================
# 🔍 RAG (Retrieval-Augmented Generation) SETTINGS
# ============================================================================
# Parameter untuk proses chunking dokumen dan retrieval dari vector store.
#
#   - CHUNK_SIZE     : Jumlah karakter maksimal per chunk saat splitting dokumen.
#                      Nilai lebih besar = konteks lebih luas per chunk, tapi
#                      kurang presisi. Default: 1000 karakter.
#   - CHUNK_OVERLAP  : Jumlah karakter overlap antar chunk berurutan.
#                      Overlap mencegah informasi terpotong di batas chunk.
#                      Default: 200 karakter.
#   - RETRIEVER_TOP_K: Jumlah chunk paling relevan yang diambil dari FAISS
#                      untuk dijadikan konteks. Default: 4 chunk.
#   - EMBEDDING_MODEL: Nama model SentenceTransformer untuk embedding teks.
#                      "all-MiniLM-L6-v2" dipilih karena ringan (~80MB) dan
#                      memiliki performa baik untuk semantic similarity.

CHUNK_SIZE: int = 1000
CHUNK_OVERLAP: int = 200
RETRIEVER_TOP_K: int = 4
EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

# ============================================================================
# 💾 MEMORY SETTINGS
# ============================================================================
# Batas maksimal jumlah pesan (human + AI) yang disimpan dalam memori
# percakapan. Pesan tertua akan dihapus jika melebihi batas ini.
# Ini mencegah context window LLM meluap pada percakapan panjang.

MAX_MEMORY_MESSAGES: int = 50

# ============================================================================
# 💬 SYSTEM PROMPTS
# ============================================================================
# System prompt menentukan persona dan perilaku AI untuk setiap jenis agent.
# Setiap agent menggunakan prompt yang berbeda sesuai fungsinya.

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

# ============================================================================
# 🌐 PROXY CONFIGURATION
# ============================================================================
# Bypass proxy untuk koneksi localhost saja.
# Ini mencegah masalah koneksi saat mengakses service lokal (misal: local LLM).
# Menggunakan setdefault() agar tidak menimpa konfigurasi proxy yang sudah ada.

os.environ.setdefault("no_proxy", "localhost,127.0.0.1")


# ============================================================================
# ✅ VALIDATION FUNCTIONS
# ============================================================================

def validate_config() -> list[str]:
    """
    Validasi konfigurasi minimum yang dibutuhkan untuk menjalankan agent.

    Memeriksa apakah variabel LLM yang wajib (API key dan base URL)
    sudah diset di file `.env`. Fungsi ini sebaiknya dipanggil di awal
    setiap agent sebelum melakukan inisialisasi LLM.

    Returns:
        list[str]: Daftar pesan error. List kosong berarti semua valid.

    Contoh:
        >>> errors = validate_config()
        >>> if errors:
        ...     for e in errors:
        ...         print(f"❌ {e}")
        ...     sys.exit(1)
        >>> print("✅ Konfigurasi valid!")
    """
    errors = []

    if not LLM_API_KEY:
        errors.append("ENOWXAI_KEY belum diset di .env")
    if not LLM_BASE_URL:
        errors.append("ENOWXAI_URL belum diset di .env")

    return errors


def validate_r2_config() -> list[str]:
    """
    Validasi konfigurasi Cloudflare R2 untuk cloud memory agent.

    Memeriksa apakah semua variabel R2 yang diperlukan sudah diset.
    Fungsi ini hanya perlu dipanggil oleh agent yang menggunakan
    fitur cloud memory (penyimpanan riwayat chat di R2).

    Returns:
        list[str]: Daftar pesan error. List kosong berarti semua valid.

    Contoh:
        >>> errors = validate_r2_config()
        >>> if errors:
        ...     print("⚠️ Cloud memory tidak tersedia:")
        ...     for e in errors:
        ...         print(f"  - {e}")
    """
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


# ============================================================================
# 🏭 FACTORY FUNCTIONS
# ============================================================================

def get_llm(temperature: float | None = None, timeout: int | None = None):
    """
    Factory function untuk membuat instance LLM (ChatOpenAI).

    Membuat dan mengembalikan instance ChatOpenAI yang sudah dikonfigurasi
    dengan parameter dari file `.env`. Parameter opsional dapat di-override
    saat pemanggilan untuk kebutuhan spesifik.

    Args:
        temperature (float | None): Override untuk tingkat kreativitas output.
            - 0.0 = output deterministik dan konsisten
            - 0.7 = default, keseimbangan kreativitas dan konsistensi
            - 1.0 = output sangat kreatif dan bervariasi
            Jika None, menggunakan nilai dari LLM_TEMPERATURE.
        timeout (int | None): Override untuk batas waktu request dalam detik.
            Jika None, menggunakan nilai dari LLM_TIMEOUT.

    Returns:
        ChatOpenAI: Instance LLM yang siap digunakan.

    Raises:
        ImportError: Jika package `langchain-openai` belum terinstal.

    Contoh:
        >>> # Menggunakan default settings
        >>> llm = get_llm()
        >>>
        >>> # Override temperature untuk output lebih kreatif
        >>> creative_llm = get_llm(temperature=0.9)
        >>>
        >>> # Override timeout untuk operasi yang membutuhkan waktu lama
        >>> patient_llm = get_llm(timeout=120)
    """
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
    """
    Factory function untuk membuat instance Embeddings (HuggingFace).

    Membuat dan mengembalikan instance HuggingFaceEmbeddings menggunakan
    model SentenceTransformer yang dikonfigurasi di EMBEDDING_MODEL.

    Model default "all-MiniLM-L6-v2" dipilih karena:
        - Ukuran ringan (~80MB download, ~22M parameter)
        - Performa baik untuk semantic similarity task
        - Berjalan di CPU tanpa masalah
        - Dimensi embedding 384 — efisien untuk FAISS

    Returns:
        HuggingFaceEmbeddings: Instance embeddings yang siap digunakan.

    Raises:
        ImportError: Jika package `langchain-huggingface` belum terinstal.

    Catatan:
        Saat pertama kali dipanggil, model akan di-download dari HuggingFace Hub.
        Setelah itu, model di-cache secara lokal sehingga tidak perlu download ulang.

    Contoh:
        >>> embeddings = get_embeddings()
        >>> vector = embeddings.embed_query("contoh teks")
        >>> print(len(vector))  # 384
    """
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)