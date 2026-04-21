# 🤖 AI Code Assistant

An intelligent AI-powered code assistant that can **read, analyze, and edit** your codebase using RAG (Retrieval-Augmented Generation) and FAISS vector search.

---

## 📁 Project Structure

```
.
├── agents/
│   ├── rag.py            # RAG Agent — tanya-jawab tentang kode (read-only)
│   └── editor.py         # Editor Agent — baca, analisis, dan edit file
├── utils/
│   ├── scanner.py        # File scanner — membaca file source code dari folder
│   └── vectorstore.py    # FAISS vector store — embedding & retrieval
├── faiss_index/          # (generated) Penyimpanan index FAISS
├── .env                  # Environment variables (API keys)
└── README.md             # Dokumentasi project
```

---

## 🚀 Features

### 🔍 RAG Agent (`agents/rag.py`)
- Scan & embed seluruh file kode dalam folder secara otomatis
- Tanya-jawab interaktif tentang codebase menggunakan konteks vektor
- Persistent FAISS index — tidak perlu re-embed setiap session
- Mode read-only — aman untuk eksplorasi tanpa risiko perubahan

### ✏️ Editor Agent (`agents/editor.py`)
- Semua kemampuan RAG Agent, **ditambah** kemampuan menulis dan mengedit file
- **3-tier smart context selection:**

| Prioritas | Kondisi | Aksi |
|-----------|---------|------|
| 1 | User menyebut file spesifik | Inject **full content** file tersebut |
| 2 | Query umum / broad | Inject **file overview** seluruh workspace |
| 3 | Query spesifik tanpa sebut file | Gunakan **RAG retrieval** |

- Safe file operations dengan validasi path (`is_safe_path`)
- Konfirmasi user sebelum setiap perubahan dieksekusi
- Parsing otomatis blok `[SAVE: path]` dari response AI

### 📂 File Scanner (`utils/scanner.py`)
- Recursive directory scan dengan filter ekstensi:
  - `.py`, `.js`, `.ts`, `.jsx`, `.tsx`, `.go`, `.html`, `.css`, `.json`, `.yaml`, `.yml`, `.md`, `.txt`, `.sh`
- Auto-skip direktori non-relevan:
  - `node_modules`, `venv`, `.venv`, `.git`, `__pycache__`, `dist`, `build`, `env`, `faiss_index`
- Skip file non-code:
  - `package-lock.json`, `yarn.lock`, `.env`, `chat_memory.json`, `memory.json`, `temp_cloud.json`
- Batas ukuran file **1MB** untuk mencegah out-of-memory

### 🧠 Vector Store (`utils/vectorstore.py`)
- FAISS-based vector similarity search
- Automatic text splitting (chunking) untuk file besar
- Setiap dokumen menyimpan metadata `source` untuk tracing asal file
- Fungsi save/load index dari disk untuk persistensi

---

## 📦 Cara Instalasi

Ikuti langkah-langkah berikut untuk menginstal dan menjalankan project ini di mesin lokal Anda.

### 1. Prasyarat (Prerequisites)

Pastikan sistem Anda sudah memiliki:

| Software | Versi Minimum | Cek Versi |
|----------|---------------|-----------|
| **Python** | 3.9+ | `python --version` |
| **pip** | 21.0+ | `pip --version` |
| **Git** | 2.0+ | `git --version` |

> 💡 **Tip:** Disarankan menggunakan Python 3.10 atau 3.11 untuk kompatibilitas terbaik dengan library FAISS dan LangChain.

### 2. Clone Repository

```bash
git clone <repo-url>
cd <project-folder>
```

### 3. Buat Virtual Environment (Disarankan)

Membuat virtual environment akan mengisolasi dependensi project agar tidak bentrok dengan package Python lain di sistem Anda.

**Linux / macOS:**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows (Command Prompt):**
```bash
python -m venv venv
venv\Scripts\activate
```

**Windows (PowerShell):**
```bash
python -m venv venv
venv\Scripts\Activate.ps1
```

> ✅ Jika berhasil, Anda akan melihat `(venv)` di awal baris terminal.

### 4. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Daftar dependensi utama yang akan terinstal:**

| Package | Fungsi |
|---------|--------|
| `langchain` | Framework LLM & chaining |
| `langchain-community` | Integrasi komunitas LangChain |
| `faiss-cpu` | Vector similarity search (FAISS) |
| `openai` / `google-generativeai` | LLM API client |
| `python-dotenv` | Membaca file `.env` |
| `tiktoken` | Tokenizer untuk embedding |

> ⚠️ Jika Anda menggunakan GPU dan ingin performa lebih cepat, ganti `faiss-cpu` dengan `faiss-gpu`:
> ```bash
> pip install faiss-gpu
> ```

### 5. Konfigurasi Environment Variables

Buat file `.env` di root project:

```bash
cp .env.example .env
```

Kemudian buka file `.env` dan isi API key yang diperlukan:

```env
# Pilih salah satu atau sesuaikan dengan LLM yang digunakan:

# OpenAI
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Google Gemini
GOOGLE_API_KEY=AIzaXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

> 🔒 **Penting:** File `.env` sudah termasuk dalam daftar file yang di-skip oleh scanner, sehingga API key Anda **tidak akan pernah ter-index** ke dalam vector store.

### 6. Verifikasi Instalasi

Jalankan perintah berikut untuk memastikan semua terinstal dengan benar:

```bash
# Cek apakah semua package terinstal
pip list | grep -E "langchain|faiss|openai|dotenv"

# Jalankan quick test
python -c "import langchain; import faiss; print('✅ Semua dependensi terinstal dengan benar!')"
```

### 7. Jalankan Agent

```bash
# RAG Agent (read-only Q&A tentang codebase)
python -m agents.rag

# Editor Agent (read + write — bisa membaca dan mengedit file)
python -m agents.editor
```

### 🔧 Troubleshooting Instalasi

<details>
<summary><b>❌ Error: <code>ModuleNotFoundError: No module named 'faiss'</code></b></summary>

```bash
pip install faiss-cpu
# atau untuk GPU:
pip install faiss-gpu
```
</details>

<details>
<summary><b>❌ Error: <code>No API key found</code></b></summary>

Pastikan file `.env` sudah ada di root project dan berisi API key yang valid. Cek juga apakah `python-dotenv` sudah terinstal:
```bash
pip install python-dotenv
```
</details>

<details>
<summary><b>❌ Error: <code>pip install gagal di Windows</code></b></summary>

Coba gunakan:
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```
Jika masih gagal, pastikan Anda menggunakan Python 3.9+ dan bukan versi Python dari Microsoft Store.
</details>

<details>
<summary><b>❌ FAISS index error saat pertama kali jalan</b></summary>

Ini normal! Saat pertama kali dijalankan, agent akan otomatis membuat folder `faiss_index/` dan melakukan embedding. Pastikan koneksi internet aktif untuk mengakses API embedding.
</details>

---

## 💬 Usage Example

```
🤖 Agent siap! Tanya apa saja tentang kode ini.
Ketik 'exit' untuk keluar.

Lu: jelaskan struktur project ini
📋 Query umum terdeteksi — menggunakan file overview...

Lu: baca file scanner.py
🎯 File spesifik terdeteksi. Membaca isi file sepenuhnya...

Lu: buatkan unit test untuk vectorstore.py
🎯 File spesifik terdeteksi. Membaca isi file sepenuhnya...

Lu: exit
```

---

## 🛡️ Safety Mechanisms

- **Path Validation** — `is_safe_path()` mencegah operasi file di luar direktori project
- **User Confirmation** — setiap perubahan file memerlukan persetujuan eksplisit
- **Excluded Files** — file sensitif (`.env`, memory/chat files) tidak pernah di-index
- **Size Limits** — file lebih dari 1MB otomatis di-skip
- **Skip Directories** — folder seperti `node_modules` dan `.git` tidak di-scan

---

## 🔄 Architecture Flow

```
User Input
    │
    ▼
┌─────────────────┐
│   Agent Layer    │
│ (rag / editor)   │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌──────────┐
│Scanner │ │ Editor   │
│(read)  │ │ (write)  │
└───┬────┘ └──────────┘
    ▼
┌──────────────┐
│ VectorStore  │
│ (embed+index)│
└───┬──────────┘
    ▼
┌──────────────┐
│ FAISS Index  │
│ (retrieve)   │
└──────────────┘
```

---

## 📄 License

MIT