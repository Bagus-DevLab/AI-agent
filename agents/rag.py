"""
agents/rag.py — Agent dengan RAG (Retrieval-Augmented Generation).
Optimasi Problem 3: Keamanan Path (Security Sandbox).
"""

import os
from langchain_core.messages import SystemMessage, HumanMessage
from config import get_llm, get_embeddings, SYSTEM_PROMPT_RAG, validate_config
from utils.scanner import scan_workspace
from utils.vectorstore import build_vectorstore, get_retriever, save_vectorstore, load_vectorstore

# Base directory ditetapkan saat startup agar konsisten
BASE_DIR = os.path.abspath(os.getcwd())


def is_safe_path(path: str) -> bool:
    """
    Memastikan path target tetap berada di dalam BASE_DIR (Security Sandbox).
    Mencegah path traversal seperti ../../etc atau path absolut di luar project.
    """
    target_abs = os.path.abspath(path)
    return target_abs.startswith(BASE_DIR)


def main(folder_path="."):
    print("=== AI CODE ANALYST (RAG) ===\n")

    # Validasi konfigurasi
    errors = validate_config()
    if errors:
        print("❌ Konfigurasi tidak lengkap:")
        for err in errors:
            print(f"   - {err}")
        return

    # Validasi keamanan path target
    if not is_safe_path(folder_path):
        print(f"❌ Akses ditolak: Folder '{folder_path}' berada di luar area project.")
        return

    # Validasi folder
    if not os.path.isdir(folder_path):
        print(f"❌ Folder tidak ditemukan: {folder_path}")
        return

    print(f"📂 Target folder: {os.path.abspath(folder_path)}")

    # Setup komponen
    llm = get_llm(temperature=0.2)
    embeddings = get_embeddings()

    vectorstore = None
    index_path = "faiss_index"

    # Cek apakah index sudah pernah dibuat sebelumnya
    if os.path.exists(index_path):
        print(f"📂 Folder '{index_path}' ditemukan.")
        pilihan = input("👉 Gunakan index yang sudah ada? (y/n): ").strip().lower()
        if pilihan == "y":
            print("📥 Memuat index dari penyimpanan lokal...")
            vectorstore = load_vectorstore(index_path)
            if not vectorstore:
                print("⚠️ Gagal memuat index lama, beralih ke scan ulang.")

    # Jika index belum ada atau user pilih scan ulang
    if not vectorstore:
        print("📥 Memproses file dan membangun index baru...")
        docs, file_count = scan_workspace(folder_path)

        if not docs:
            print("❌ Tidak ada file kodingan yang ditemukan di folder ini.")
            return

        print(f"✅ Berhasil membaca {file_count} file. Memulai embedding...")
        vectorstore = build_vectorstore(docs, embeddings)

        # Simpan index agar bisa dipakai lagi nanti
        save_vectorstore(vectorstore, index_path)

    retriever = get_retriever(vectorstore)

    print("\n🤖 RAG Agent siap! Tanya apa saja tentang kode ini.")
    print("Ketik 'exit' untuk keluar.\n")

    while True:
        try:
            user_input = input("Lu: ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if user_input.lower() in ["exit", "quit"]:
            break
        if not user_input:
            continue

        print("🔍 Mencari konteks relevan...")
        relevant_docs = retriever.invoke(user_input)

        context_parts = []
        for doc in relevant_docs:
            source = doc.metadata.get("source", "unknown")
            context_parts.append(f"// File: {source}\n{doc.page_content}")

        context = "\n\n---\n\n".join(context_parts)

        messages = [
            SystemMessage(content=SYSTEM_PROMPT_RAG),
            HumanMessage(
                content=f"Konteks kodingan terkait (RAG):\n{context}\n\n---\n\nPertanyaan user:\n{user_input}"
            ),
        ]

        print("AI sedang berpikir...")
        try:
            response = llm.invoke(messages)
            print(f"\nAI: {response.content}\n")
        except Exception as e:
            print(f"❌ Error: {e}\n")


if __name__ == "__main__":
    main()