import os
import sys
import re
import shutil
import subprocess
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# Pastikan proxy tidak mengganggu request lokal ke model embedding
os.environ["no_proxy"] = "*"

# ==========================================
# 1. SETUP LLM (Claude via Proxy Lu)
# ==========================================
llm = ChatOpenAI(
    api_key="enx-0ffdb0f80efd7d1b8972e84e7037900b4f64b33c0631ea07ed1821db9b7549d2", 
    base_url="http://172.20.32.1:1430/v1", 
    model="claude-opus-4.6",
    temperature=0.2, # Rendah agar kode yang dihasilkan stabil/akurat
    timeout=120 
)

# ==========================================
# 2. SETUP EMBEDDING LOKAL (Free & Fast)
# ==========================================
print("📥 Memuat model pembaca teks lokal (HuggingFace)...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# ==========================================
# 3. PEMINDAIAN FOLDER DINAMIS (Anti-Venv)
# ==========================================
folder_path = sys.argv[1] if len(sys.argv) > 1 else "."
print(f"📂 Memindai kodingan di dalam '{folder_path}'...")

forbidden_dirs = {"venv", ".git", "node_modules", "__pycache__", ".cache", "build", "dist"}
allowed_exts = {".py", ".go", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".md", ".txt", ".sh", ".php"}

docs = []
loaded_files = [] # Menyimpan daftar struktur file secara global
file_count = 0

for root, dirs, files in os.walk(folder_path):
    # Skip folder yang tidak perlu dengan memodifikasi list 'dirs' secara langsung
    dirs[:] = [d for d in dirs if d not in forbidden_dirs]
    
    for file in files:
        ext = os.path.splitext(file)[1].lower()
        if ext in allowed_exts:
            file_path = os.path.join(root, file)
            try:
                loader = TextLoader(file_path, encoding='utf-8')
                loaded_docs = loader.load()
                for doc in loaded_docs:
                    # Menambahkan metadata path langsung ke teks agar AI tahu lokasi filenya
                    doc.page_content = f"// File Path: {file_path}\n" + doc.page_content
                docs.extend(loaded_docs)
                loaded_files.append(file_path) # Daftarkan file ini
                file_count += 1
            except Exception:
                # Abaikan file yang gagal dibaca (misal karena encoding tidak didukung)
                continue

if len(docs) == 0:
    print(f"❌ Gagal: Tidak ada file kodingan yang terbaca di direktori ini.")
    sys.exit()

print(f"✅ Berhasil memuat {file_count} file kodingan ke memori.")

# ==========================================
# 4. PENYUSUNAN VECTOR STORE (FAISS)
# ==========================================
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
splits = text_splitter.split_documents(docs)

print("🧠 Menyusun indeks pencarian...")
vectorstore = FAISS.from_documents(documents=splits, embedding=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

# ==========================================
# 5. LOOP INTERAKTIF AGENT
# ==========================================
print(f"\n🚀 === AI AGENT (FULL STACK + DEVOPS) SIAP! === 🚀")
print("Perintah yang bisa dilakukan bot:")
print("1. Tanya jawab / Refactor kode")
print("2. Manajemen File (Bikin, Hapus, Pindah)")
print("3. Eksekusi Terminal (git commit, npm install, dll - Butuh persetujuan lu)")
print("Ketik 'exit' untuk keluar.\n")

chat_history = []

while True:
    # Menggunakan .strip() agar spasi kosong atau karakter aneh (seperti pencetan panah) terbersihkan
    pertanyaan = input("Lu: ").strip() 
    
    # Cegah request kosong yang membuat API Error 400
    if not pertanyaan: 
        continue

    if pertanyaan.lower() in ['exit', 'quit']:
        print("👋 Sampai jumpa!")
        break
    
    print("AI sedang memikirkan dan menganalisis kode...")
    try:
        # Mencari context kodingan yang relevan berdasarkan pertanyaan
        docs_found = retriever.invoke(pertanyaan)
        konteks = "\n\n".join(doc.page_content for doc in docs_found)
        
        # Susun daftar file menjadi teks agar AI tahu isi folder secara global
        struktur_project = "\n".join([f"- {f}" for f in loaded_files])
        
        # PROMPT INSTRUKSI KHUSUS UNTUK MANAJEMEN FILE & TERMINAL
        system_prompt = f"""Kamu adalah Senior AI Programmer dan DevOps Engineer. 

INFORMASI PROJECT SAAT INI:
Berikut adalah daftar {file_count} file kodingan yang ada di workspace user saat ini:
{struktur_project}

Gunakan konteks kodingan (hasil RAG) berikut untuk membantu menjawab pertanyaan user tentang detail kode:
{konteks}

ATURAN MANAJEMEN FILE DAN TERMINAL:
Kamu memiliki kemampuan penuh untuk memanipulasi file dan mengeksekusi perintah terminal. 
Kamu WAJIB menggunakan format tag khusus berikut agar sistem bisa mengeksekusinya:

1. UNTUK MEMBUAT FILE BARU ATAU MENGEDIT FILE YANG ADA:
[SAVE: path/menuju/nama_file.ext]
```language
// KODE FULL DISINI
```

2. UNTUK MENGHAPUS FILE:
[DELETE: path/menuju/nama_file.ext]

3. UNTUK MEMINDAHKAN ATAU RENAME FILE:
[MOVE: path/lama/file.ext -> path/baru/file.ext]

4. UNTUK MENJALANKAN PERINTAH TERMINAL:
[RUN: perintah_yang_ingin_dijalankan]
(Contoh: [RUN: git status] atau [RUN: npm install axios])

CATATAN PENTING:
- Jika kamu menggunakan tag [SAVE], kamu HARUS memberikan keseluruhan isi file tanpa dipotong. Jangan gunakan placeholder seperti "sisa kode sebelumnya ada disini".
- Kamu bisa menggunakan lebih dari satu tag dalam satu jawaban. Misalnya, membuat file lalu menjalankan git commit.
"""
        
        # Siapkan struktur pesan untuk LLM
        messages = [SystemMessage(content=system_prompt)]
        
        # Masukkan memori percakapan sebelumnya (batas 6 pesan terakhir agar hemat token & fokus)
        for msg in chat_history[-6:]:
            messages.append(msg)
            
        # Masukkan pertanyaan saat ini
        messages.append(HumanMessage(content=pertanyaan))
        
        # Panggil LLM
        response = llm.invoke(messages)
        jawaban = response.content
        
        print(f"\nAI: \n{jawaban}\n")
        
        # Simpan ke riwayat percakapan
        chat_history.append(HumanMessage(content=pertanyaan))
        chat_history.append(AIMessage(content=jawaban))
        
        # ==========================================
        # 6. PARSING DAN EKSEKUSI PERINTAH
        # ==========================================
        
        # A. Logika SAVE (Membuat/Mengedit File)
        pattern_save = r"\[SAVE:\s*(.+?)\]\s*```[a-zA-Z]*\n(.*?)```"
        matches_save = re.findall(pattern_save, jawaban, re.DOTALL)
        
        for filepath, code_content in matches_save:
            filepath = filepath.strip()
            print(f"⏳ Mengeksekusi pembuatan/perubahan file: {filepath}")
            try:
                folder_tujuan = os.path.dirname(filepath)
                if folder_tujuan:
                    os.makedirs(folder_tujuan, exist_ok=True)
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(code_content)
                print(f"✅ Berhasil menyimpan: {filepath}")
            except Exception as e:
                print(f"❌ Gagal menyimpan {filepath}: {e}")

        # B. Logika DELETE (Menghapus File)
        pattern_delete = r"\[DELETE:\s*(.+?)\]"
        matches_delete = re.findall(pattern_delete, jawaban)
        
        for filepath in matches_delete:
            filepath = filepath.strip()
            print(f"⏳ Mengeksekusi penghapusan file: {filepath}")
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    print(f"🗑️ Berhasil menghapus: {filepath}")
                else:
                    print(f"⚠️ File tidak ditemukan: {filepath}")
            except Exception as e:
                print(f"❌ Gagal menghapus {filepath}: {e}")

        # C. Logika MOVE (Memindahkan/Rename File)
        pattern_move = r"\[MOVE:\s*(.+?)\s*->\s*(.+?)\]"
        matches_move = re.findall(pattern_move, jawaban)
        
        for old_path, new_path in matches_move:
            old_path = old_path.strip()
            new_path = new_path.strip()
            print(f"⏳ Memindahkan dari {old_path} ke {new_path}")
            try:
                if os.path.exists(old_path):
                    folder_tujuan = os.path.dirname(new_path)
                    if folder_tujuan:
                        os.makedirs(folder_tujuan, exist_ok=True)
                        
                    shutil.move(old_path, new_path)
                    print(f"🚚 Berhasil memindahkan file ke: {new_path}")
                else:
                    print(f"⚠️ File sumber tidak ditemukan: {old_path}")
            except Exception as e:
                print(f"❌ Gagal memindahkan {old_path}: {e}")

        # D. Logika RUN (Menjalankan Perintah Terminal)
        pattern_run = r"\[RUN:\s*(.+?)\]"
        matches_run = re.findall(pattern_run, jawaban)
        
        for cmd in matches_run:
            cmd = cmd.strip()
            print(f"\n⚠️  PERINGATAN TERMINAL!")
            print(f"🤖 AI meminta izin untuk mengeksekusi perintah berikut:")
            print(f"👉 \033[93m{cmd}\033[0m") # Teks warna kuning untuk highlight command
            
            # FITUR KEAMANAN: Wajib konfirmasi user
            konfirmasi = input("Izinkan eksekusi? (y/n): ").strip().lower()
            
            if konfirmasi == 'y':
                print(f"⏳ Mengeksekusi: {cmd} ...")
                try:
                    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
                    
                    if result.stdout:
                        print(f"✅ Output Terminal:\n{result.stdout.strip()}")
                        # Memasukkan output sukses ke memori AI (opsional)
                        chat_history.append(SystemMessage(content=f"Hasil eksekusi '{cmd}' sukses:\n{result.stdout}"))
                        
                    if result.stderr:
                        print(f"❌ Error Terminal:\n{result.stderr.strip()}")
                        # Memasukkan output error ke memori AI agar dia tahu salahnya dimana
                        chat_history.append(SystemMessage(content=f"Hasil eksekusi '{cmd}' gagal dengan error:\n{result.stderr}"))
                        
                except Exception as e:
                    print(f"❌ Sistem gagal menjalankan perintah: {e}")
            else:
                print("🛑 Eksekusi dibatalkan oleh user.")
                chat_history.append(SystemMessage(content=f"User membatalkan eksekusi perintah '{cmd}'."))
                
    except Exception as e:
        print(f"❌ Terjadi kesalahan pada sistem agen: {e}")