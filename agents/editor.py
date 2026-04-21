"""
agents/editor.py — Agent Editor dengan optimasi RAG (Problem 1 Fix).
Hanya mengambil potongan kode yang relevan untuk menghemat token.
"""

import os
import re
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from config import get_llm, get_embeddings, SYSTEM_PROMPT_EDITOR
from utils.scanner import scan_workspace
from utils.vectorstore import build_vectorstore, get_retriever

# Base directory project — semua operasi file dibatasi di sini
BASE_DIR = os.path.abspath(os.getcwd())


def is_safe_path(filepath: str) -> bool:
    """
    Memastikan filepath target tetap berada di dalam BASE_DIR (Security Sandbox).
    Mencegah path traversal seperti ../../etc/passwd atau path absolut di luar project.
    """
    target_abs = os.path.abspath(filepath)
    return target_abs.startswith(BASE_DIR)


def execute_file_operations(ai_response):
    """Mencari dan mengeksekusi perintah manipulasi file dengan konfirmasi."""
    changes_made = []
    
    # 1. Logika SAVE
    save_pattern = r"\[SAVE:\s*(.+?)\]\s*```[a-zA-Z]*\n(.*?)```"
    save_matches = re.findall(save_pattern, ai_response, re.DOTALL)
    for filepath, content in save_matches:
        filepath = filepath.strip()

        # SECURITY FIX: Validasi path sebelum menyimpan
        if not is_safe_path(filepath):
            print(f"🚫 Ditolak: '{filepath}' berada di luar area project. Operasi dibatalkan.")
            continue

        konfirmasi = input(f"\n💾 Simpan perubahan ke '{filepath}'? (y/n): ").strip().lower()
        if konfirmasi == 'y':
            try:
                # BUG FIX: Gunakan os.path.dirname yang aman untuk semua kasus
                parent_dir = os.path.dirname(os.path.abspath(filepath))
                os.makedirs(parent_dir, exist_ok=True)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"✅ Berhasil mengupdate {filepath}")
                changes_made.append(f"SAVE: {filepath}")
            except Exception as e:
                print(f"❌ Gagal menyimpan {filepath}: {e}")

    # 2. Logika DELETE
    delete_pattern = r"\[DELETE:\s*(.+?)\]"
    delete_matches = re.findall(delete_pattern, ai_response)
    for filepath in delete_matches:
        filepath = filepath.strip()

        # SECURITY FIX: Validasi path sebelum menghapus
        if not is_safe_path(filepath):
            print(f"🚫 Ditolak: '{filepath}' berada di luar area project. Operasi dibatalkan.")
            continue

        konfirmasi = input(f"\n🗑️  Hapus file '{filepath}'? (y/n): ").strip().lower()
        if konfirmasi == 'y' and os.path.exists(filepath):
            os.remove(filepath)
            print(f"✅ Berhasil menghapus {filepath}")
            changes_made.append(f"DELETE: {filepath}")

    return changes_made

def main(folder_path="."):
    print(f"=== 🛠️  AI SMART EDITOR (RAG ENABLED) ===\n📂 Workspace: {folder_path}")
    
    # Inisialisasi Komponen
    llm = get_llm(temperature=0.2)
    embeddings = get_embeddings()
    
    # Membangun Indeks Kodingan di Awal agar AI punya 'peta' kodingan
    print("📥 Scanning dan indexing kodingan...")
    docs, count = scan_workspace(folder_path)
    vectorstore = build_vectorstore(docs, embeddings)
    retriever = get_retriever(vectorstore, top_k=5) # Ambil 5 potongan paling relevan
    
    chat_history = [SystemMessage(content=SYSTEM_PROMPT_EDITOR)]
    print(f"✅ {count} file berhasil di-index. Siap menerima perintah.")

    while True:
        try:
            user_input = input("\nLu: ").strip()
        except KeyboardInterrupt:
            break
            
        if user_input.lower() in ["exit", "quit"]:
            break
        if not user_input:
            continue

        # STEP CRUCIAL: Retrieve hanya kode yang nyambung dengan pertanyaan lo
        print("🔍 Mencari referensi kode yang relevan...")
        relevant_chunks = retriever.invoke(user_input)
        
        context_parts = []
        for doc in relevant_chunks:
            source = doc.metadata.get("source", "unknown")
            context_parts.append(f"// File: {source}\n{doc.page_content}")
        
        context_str = "\n\n---\n\n".join(context_parts)
        
        # Susun Prompt Dinamis
        prompt = f"REFERENSI KODE RELEVAN:\n{context_str}\n\nINSTRUKSI USER: {user_input}"
        chat_history.append(HumanMessage(content=prompt))

        print("AI sedang menganalisis...")
        try:
            response = llm.invoke(chat_history)
            ai_text = response.content
            print(f"\nAI:\n{ai_text}\n")

            # Eksekusi aksi jika ada
            if execute_file_operations(ai_text):
                # Opsional: Re-index jika ada perubahan struktur yang masif
                print("🔄 Catatan: File telah berubah. Jalankan ulang editor jika ingin refresh index.")
            
            chat_history.append(AIMessage(content=ai_text))
            
        except Exception as e:
            print(f"❌ Terjadi kesalahan: {e}")

if __name__ == "__main__":
    main()