# AI Code Assistant

AI-powered code assistant dengan 5 agent mode: basic chat, memory, RAG analysis, file editor, dan cloud memory. Dibangun dengan LangChain, FAISS vector search, dan Cloudflare R2.

---

## Project Structure

```
.
├── main.py                  # Entry point — menu pemilihan agent
├── config.py                # Konfigurasi terpusat (env, LLM, R2, prompts)
├── agents/
│   ├── basic.py             # [1] Test koneksi LLM
│   ├── memory.py            # [2] Chat dengan memori lokal
│   ├── rag.py               # [3] RAG — analisis codebase (read-only)
│   ├── editor.py            # [4] Editor — baca, analisis, & edit file
│   └── cloud.py             # [5] Chat dengan memori Cloudflare R2
├── utils/
│   ├── scanner.py           # Recursive file scanner dengan filtering
│   ├── vectorstore.py       # FAISS vector store (embed, save, load, retrieve)
│   ├── memory.py            # Load/simpan memori percakapan lokal
│   └── security.py          # Shared path validation (security sandbox)
├── tests/                   # Test suite (pytest, 153 tests)
│   ├── conftest.py          # Shared fixtures
│   ├── test_scanner.py      # Scanner & filtering tests
│   ├── test_security.py     # Direct security function tests
│   ├── test_rag_security.py # RAG agent security wrapper tests
│   ├── test_editor_security.py  # Editor security, parsing, query detection
│   ├── test_editor_memory.py    # Editor memory load/save tests
│   ├── test_memory.py       # Local memory load/save/trim tests
│   └── test_config.py       # Config validation tests
├── .env                     # Environment variables (tidak di-track git)
├── .env.example             # Template environment variables
├── requirements.txt         # Python dependencies
└── pytest.ini               # Pytest configuration
```

---

## Agents

### [1] Basic — Test Koneksi LLM

Kirim satu pesan ke LLM untuk verifikasi koneksi API berfungsi.

### [2] Memory — Chat dengan Memori Lokal

Chat interaktif dengan persistent memory. Riwayat percakapan disimpan ke `chat_memory.json` dan dimuat ulang di sesi berikutnya. Sliding window membatasi jumlah pesan agar tidak melebihi context window LLM.

### [3] RAG — Analisis Codebase (Read-Only)

Scan seluruh file source code, embed ke FAISS vector store, lalu jawab pertanyaan berdasarkan konteks kode yang relevan. Index disimpan ke disk (`faiss_index/`) untuk persistensi.

### [4] Editor — Baca & Edit File

Semua kemampuan RAG, ditambah kemampuan menulis dan mengedit file. Smart context selection:

| Prioritas | Kondisi | Aksi |
|-----------|---------|------|
| 1 | User menyebut file spesifik | Inject full content file |
| 2 | Query umum / broad | Inject file overview workspace |
| 3 | Query spesifik tanpa sebut file | RAG retrieval |

File operations menggunakan format `[SAVE: path]...[/SAVE]` dan `[DELETE: path]`, dengan konfirmasi user sebelum eksekusi.

### [5] Cloud — Chat dengan Memori R2

Sama seperti Memory agent, tapi riwayat percakapan disimpan di Cloudflare R2 (S3-compatible). Memori di-download saat mulai dan di-upload saat keluar.

---

## Instalasi

### Prasyarat

| Software | Versi Minimum |
|----------|---------------|
| Python | 3.10+ |
| pip | 21.0+ |

### Setup

```bash
# Clone & masuk ke project
git clone <repo-url>
cd <project-folder>

# Buat virtual environment
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Konfigurasi

Buat file `.env` dari template:

```bash
cp .env.example .env
```

Isi variabel yang diperlukan:

```env
# LLM Configuration
ENOWXAI_KEY=your_api_key_here
ENOWXAI_URL=https://your-llm-endpoint/v1
ENOWXAI_MODEL=claude-opus-4.6

# Cloudflare R2 (opsional, hanya untuk agent Cloud)
R2_ACCESS_KEY=your_access_key
R2_SECRET_KEY=your_secret_key
R2_ENDPOINT=https://your-account.r2.cloudflarestorage.com
R2_BUCKET_NAME=your-bucket-name
```

---

## Cara Menjalankan

```bash
python main.py
```

Menu interaktif akan muncul:

```
╔══════════════════════════════════════════╗
║         AI AGENT LAUNCHER               ║
╠══════════════════════════════════════════╣
║                                          ║
║  [1] Basic    — Test koneksi LLM         ║
║  [2] Memory   — Chat dengan memori lokal ║
║  [3] RAG      — Analisis codebase        ║
║  [4] Editor   — Baca & edit file         ║
║  [5] Cloud    — Chat dengan memori R2    ║
║                                          ║
║  [0] Exit                                ║
║                                          ║
╚══════════════════════════════════════════╝
```

Agent [3] RAG dan [4] Editor akan meminta path folder yang ingin di-scan.

### Perintah dalam sesi interaktif

| Perintah | Fungsi |
|----------|--------|
| Ketik pertanyaan | AI menjawab berdasarkan konteks |
| Sebut nama file (misal: `baca scanner.py`) | AI membaca full content file |
| `reindex` (RAG only) | Rebuild FAISS index |
| `clear` (Memory/Editor) | Hapus riwayat percakapan |
| `exit` / `quit` | Keluar dari agent |

---

## Testing

Project ini memiliki 153 test yang mencakup scanner, security, memory, config, dan editor parsing.

```bash
# Jalankan semua test
python -m pytest

# Verbose output
python -m pytest -v

# Jalankan test spesifik
python -m pytest -k scanner
python -m pytest -k security
python -m pytest -k editor
```

---

## Security

- **Path Sandbox** — `is_safe_path()` di `utils/security.py` mencegah operasi file di luar workspace. Resolve symlinks dan cegah prefix bypass attack.
- **User Confirmation** — setiap SAVE/DELETE memerlukan konfirmasi eksplisit.
- **Secret Protection** — semua varian `.env` (`.env`, `.env.*`) di-skip dari scanning dan tidak pernah ter-index ke vector store.
- **Size Limit** — file > 1MB otomatis di-skip.
- **Directory Filtering** — `node_modules`, `.git`, `venv`, `__pycache__`, dll. tidak di-scan.

---

## Architecture

```
User Input
    |
    v
+------------------+
|   main.py        |  Menu & routing
+--------+---------+
         |
   +-----+------+------+------+------+
   v     v      v      v      v
Basic  Memory   RAG   Editor  Cloud    <- agents/
                 |      |
           +-----+------+
           v             v
      Scanner        Security          <- utils/
           |
           v
      VectorStore
           |
           v
      FAISS Index (disk)
```

---

## Dependencies

| Package | Fungsi |
|---------|--------|
| `langchain` | Framework LLM & chaining |
| `langchain-openai` | OpenAI-compatible LLM client |
| `langchain-community` | FAISS integration |
| `faiss-cpu` | Vector similarity search |
| `tiktoken` | Tokenizer untuk embeddings |
| `python-dotenv` | Membaca file `.env` |
| `boto3` | Cloudflare R2 (S3-compatible) client |

---

## License

MIT
