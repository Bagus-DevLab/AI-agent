import os
import sys
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

os.environ["no_proxy"] = "*"

# 1. Setup LLM Utama 
llm = ChatOpenAI(
    api_key="enx-0ffdb0f80efd7d1b8972e84e7037900b4f64b33c0631ea07ed1821db9b7549d2", 
    base_url="http://172.20.32.1:1430/v1", 
    model="claude-opus-4.6",
    temperature=0.2, 
    timeout=60
)

# 2. Setup Embedding Lokal
print("📥 Memuat model pembaca teks lokal...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 3. Baca Folder Kodingan Dinamis (CARA BARU ANTI-JEBOL)
folder_path = sys.argv[1] if len(sys.argv) > 1 else "."
print(f"📂 Memindai kodingan di dalam {folder_path}...")

# Daftar folder yang HARAM dibaca
forbidden_dirs = {"venv", ".git", "node_modules", "__pycache__", ".cache", "build", "dist"}
# Daftar ekstensi file kodingan yang HALAL dibaca (lu bisa tambahin kalau ada yang kurang)
allowed_exts = {".py", ".go", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".md", ".txt", ".sh", ".php"}

docs = []
file_count = 0

# Kita sweeping file-nya manual pake OS bawaan Python (Jauh lebih cepat & aman)
for root, dirs, files in os.walk(folder_path):
    # Usir folder terlarang biar gak ikut ke-scan
    dirs[:] = [d for d in dirs if d not in forbidden_dirs]
    
    for file in files:
        ext = os.path.splitext(file)[1].lower()
        # Kalau file ini adalah kodingan yang kita kenal
        if ext in allowed_exts:
            file_path = os.path.join(root, file)
            try:
                # Load sebagai teks biasa
                loader = TextLoader(file_path, encoding='utf-8')
                docs.extend(loader.load())
                file_count += 1
            except Exception:
                continue # Kalau file-nya rusak, skip diem-diem

if len(docs) == 0:
    print(f"❌ Gagal: Tidak ada file kodingan dengan ekstensi yang diizinkan di direktori ini.")
    sys.exit()

print(f"✅ Aman! Berhasil memuat HANYA {file_count} file kodingan.")

# 4. Potong-potong file
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
splits = text_splitter.split_documents(docs)

# 5. Simpan ke Database FAISS
print("🧠 Sedang menyusun ingatan kodingan...")
vectorstore = FAISS.from_documents(documents=splits, embedding=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

print(f"\n🚀 === AI RAG SIAP! ({folder_path}) === 🚀")
print("Ketik 'exit' untuk keluar.\n")

while True:
    pertanyaan = input("Lu: ")
    if pertanyaan.lower() == 'exit':
        break
    
    print("AI sedang mencari kodingan yang relevan...")
    try:
        docs_found = retriever.invoke(pertanyaan)
        konteks_kodingan = "\n\n".join(doc.page_content for doc in docs_found)
        
        pesan = [
            SystemMessage(content=(
                "Kamu adalah AI Asisten Programmer yang ahli. "
                "Jawablah pertanyaan user HANYA berdasarkan konteks kodingan di bawah ini. "
                "Jika jawabannya tidak ada di dalam konteks, katakan 'Saya tidak menemukan informasinya di file project'.\n\n"
                f"=== KONTEKS KODINGAN ===\n{konteks_kodingan}"
            )),
            HumanMessage(content=pertanyaan)
        ]
        
        print("AI sedang merumuskan jawaban...")
        response = llm.invoke(pesan)
        print(f"\nAI: {response.content}\n")
        
    except Exception as e:
        print(f"Error: {e}")