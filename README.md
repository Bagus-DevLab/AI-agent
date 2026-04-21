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

## ⚙️ Setup

1. **Clone repository**
   ```bash
   git clone <repo-url>
   cd <project-folder>
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Konfigurasi environment**
   ```bash
   cp .env.example .env
   # Edit .env dan masukkan API key yang diperlukan
   ```

4. **Jalankan agent**
   ```bash
   # RAG Agent (read-only Q&A)
   python -m agents.rag

   # Editor Agent (read + write)
   python -m agents.editor
   ```

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
---