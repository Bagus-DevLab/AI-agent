"""
agents/rag.py — Agent dengan RAG (Retrieval-Augmented Generation).
Menganalisis codebase menggunakan semantic search.
"""

import os
from langchain_core.messages import SystemMessage, HumanMessage
from config import get_llm, get_embeddings, SYSTEM_PROMPT_RAG, validate_config
from utils.scanner import scan_workspace
from utils.vectorstore import build_vectorstore, get_retriever, save_vectorstore


def main(folder_path="."):
    print("=== AI CODE ANALYST (RAG) ===\n")

    # Validasi konfigurasi
    errors = validate_config()
    if errors:
        print("❌ Konfigurasi tidak lengkap:")
        for err in errors:
            print(f"   - {err}")
        return

    # Validasi folder
    if not os.path.isdir(folder_path):
        print(f"❌ Folder tidak ditemukan: {folder_path}")
        return

    print(f"📂 Target folder: {os.path.abspath(folder_path)}")

    # Setup komponen
    llm = get_llm(temperature=0.2)
    embeddings = get_embeddings()

    # Scan & build vectorstore (sekali saja, tidak duplikasi)
    print("📥 Memuat dan memproses file...")
    docs, file_count = scan_workspace(folder_path)

    if not docs:
        print("❌ Tidak ada file kodingan yang ditemukan di folder ini.")
        return

    print(f"✅ Berhasil membaca {file_count} file.\n")

    vectorstore = build_vectorstore(docs, embeddings)

    # Simpan index untuk penggunaan di masa depan
    save_vectorstore(vectorstore)

    retriever = get_retriever(vectorstore)

    print("\n🤖 RAG Agent siap! Tanya apa saja tentang kode ini.")
    print("Ketik 'exit' untuk keluar.\n")

    while True:
        try:
            user_input = input("Lu: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Bye!")
            break

        if user_input.lower() == "exit":
            print("👋 Bye!")
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
