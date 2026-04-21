"""
agents/rag.py — Agent dengan RAG (Retrieval-Augmented Generation).
"""

import sys
from langchain_core.messages import SystemMessage, HumanMessage
from config import get_llm, get_embeddings, SYSTEM_PROMPT_RAG
from utils.scanner import scan_workspace, get_file_list
from utils.vectorstore import build_vectorstore, get_retriever, save_vectorstore


def main(folder_path="."):
    print("=== AI CODE ANALYST (RAG) ===\n")
    print(f"📂 Target folder: {folder_path}")

    # Tampilkan daftar file
    file_list = get_file_list(folder_path)
    if not file_list:
        print("❌ Tidak ada file kodingan yang ditemukan.")
        return

    # Setup komponen
    llm = get_llm(temperature=0.2)
    embeddings = get_embeddings()

    # Scan & build vectorstore
    print("📥 Memuat dan memproses file...")
    docs, file_count = scan_workspace(folder_path)
    print(f"✅ Berhasil membaca {file_count} file.\n")

    if not docs:
        print("❌ Gagal mendapatkan konten file.")
        return

    vectorstore = build_vectorstore(docs, embeddings)
    
    # Simpan index untuk penggunaan di masa depan
    save_vectorstore(vectorstore)

    retriever = get_retriever(vectorstore)

    print("\n🤖 RAG Agent siap! Tanya apa saja tentang kode ini.")
    print("Ketik 'exit' untuk keluar.\n")

    while True:
        try:
            user_input = input("Lu: ").strip()
        except KeyboardInterrupt:
            break

        if user_input.lower() == "exit":
            break
        if not user_input:
            continue

        print("🔍 Mencari konteks relevan...")
        relevant_docs = retriever.invoke(user_input)

        context_parts = []
        for doc in relevant_docs:
            source = doc.metadata.get("source", "unknown")
            context_parts.append(f"// File Path: {source}\n{doc.page_content}")

        context = "\n\n---\n\n".join(context_parts)

        messages = [
            SystemMessage(content=SYSTEM_PROMPT_RAG),
            HumanMessage(content=f"Konteks kodingan terkait (RAG):\n{context}\n\n---\n\nPertanyaan user:\n{user_input}"),
        ]

        print("AI sedang berpikir...")
        try:
            response = llm.invoke(messages)
            print(f"\nAI: {response.content}\n")
        except Exception as e:
            print(f"❌ Error: {e}\n")

if __name__ == "__main__":
    main()