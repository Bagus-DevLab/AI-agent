"""
rag.py — Agent dengan RAG (Retrieval-Augmented Generation).
Membaca seluruh codebase lalu menjawab pertanyaan berdasarkan kode.
Pengganti agent_rag.py yang sudah di-refactor.

Usage: python -m agents.rag [folder_path]
"""

import sys
from langchain_core.messages import SystemMessage, HumanMessage
from config import get_llm, get_embeddings, SYSTEM_PROMPT_RAG
from utils.scanner import scan_workspace, get_file_list
from utils.vectorstore import build_vectorstore, get_retriever, save_vectorstore


def main():
    print("=== AI CODE ANALYST (RAG) ===\n")

    # Tentukan folder target
    folder_path = sys.argv[1] if len(sys.argv) > 1 else "."
    print(f"📂 Target folder: {folder_path}")

    # Tampilkan daftar file
    file_list = get_file_list(folder_path)
    print(f"📄 Ditemukan {len(file_list)} file kodingan:")
    for f in file_list:
        print(f"   - {f}")
    print()

    # Setup komponen
    llm = get_llm(temperature=0.2)
    embeddings = get_embeddings()

    # Scan & build vectorstore
    print("📥 Memuat dan memproses file...")
    docs, file_count = scan_workspace(folder_path)
    print(f"✅ Berhasil membaca {file_count} file.\n")

    if not docs:
        print("❌ Tidak ada file yang bisa dibaca. Keluar.")
        return

    vectorstore = build_vectorstore(docs, embeddings)
    if not vectorstore:
        print("❌ Gagal membangun vector database. Keluar.")
        return

    # Simpan vectorstore ke disk
    save_vectorstore(vectorstore)

    retriever = get_retriever(vectorstore)

    print("\n🤖 RAG Agent siap! Tanya apa saja tentang kode ini.")
    print("Ketik 'exit' untuk keluar.\n")

    while True:
        user_input = input("Lu: ")
        if user_input.lower() == "exit":
            print("Bye! 👋")
            break

        # Retrieve konteks yang relevan
        print("🔍 Mencari konteks relevan...")
        relevant_docs = retriever.invoke(user_input)

        # Bangun konteks dari hasil retrieval
        context_parts = []
        for i, doc in enumerate(relevant_docs, 1):
            source = doc.metadata.get("source", "unknown")
            context_parts.append(f"// File Path: {source}\n{doc.page_content}")

        context = "\n\n---\n\n".join(context_parts)

        # Kirim ke LLM dengan konteks
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
