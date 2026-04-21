"""
agents/rag.py — Agent dengan RAG (Retrieval-Augmented Generation).
Optimasi Problem 3: Keamanan Path (Security Sandbox).
"""

import os
from langchain_core.messages import SystemMessage, HumanMessage
from config import get_llm, get_embeddings, SYSTEM_PROMPT_RAG, validate_config, BASE_DIR
from utils.scanner import scan_workspace
from utils.vectorstore import build_vectorstore, get_retriever, save_vectorstore, load_vectorstore

# Gunakan BASE_DIR dari config agar konsisten (bukan os.getcwd() saat import)


def is_safe_path(path: str) -> bool:
    """
    Memastikan path target tetap berada di dalam BASE_DIR (Security Sandbox).
    
    FIX 1: Gunakan os.path.realpath() untuk resolve symlinks.
    FIX 2: Gunakan os.sep untuk mencegah prefix bypass 
           (e.g., /home/user/project_evil vs /home/user/project).
    """
    # Resolve symlinks DAN normalize path
    target_abs = os.path.realpath(os.path.abspath(path))
    base_abs = os.path.realpath(BASE_DIR)

    # Pastikan path berada di dalam BASE_DIR dengan separator check
    # Ini mencegah /home/user/project_evil lolos dari check /home/user/project
    return target_abs == base_abs or target_abs.startswith(base_abs + os.sep)


def main():
    print("=== RAG AGENT ===\n")

    # Validasi konfigurasi
    errors = validate_config()
    if errors:
        print("❌ Konfigurasi tidak lengkap:")
        for err in errors:
            print(f"   - {err}")
        return

    llm = get_llm()
    embeddings = get_embeddings()

    # Coba load existing vectorstore, atau buat baru
    print("📂 Memuat workspace...")
    vectorstore = load_vectorstore(embeddings)

    if vectorstore is None:
        print("🔨 Membuat index baru...")
        docs, count = scan_workspace(BASE_DIR)
        if not docs:
            print("❌ Tidak ada file yang ditemukan untuk di-index.")
            return
        vectorstore = build_vectorstore(docs, embeddings)
        save_vectorstore(vectorstore)
        print(f"✅ {count} dokumen berhasil di-index.")
    else:
        print("✅ Index berhasil dimuat dari cache.")

    retriever = get_retriever(vectorstore)

    print("\n🤖 Agent siap! Tanya apa saja tentang kode ini.")
    print("Ketik 'exit' untuk keluar, 'reindex' untuk rebuild index.\n")

    while True:
        try:
            user_input = input("Lu: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Bye!")
            break

        if not user_input:
            continue

        if user_input.lower() == "exit":
            print("👋 Bye!")
            break

        if user_input.lower() == "reindex":
            print("🔨 Rebuilding index...")
            docs, count = scan_workspace(BASE_DIR)
            if not docs:
                print("❌ Tidak ada file yang ditemukan.")
                continue
            vectorstore = build_vectorstore(docs, embeddings)
            save_vectorstore(vectorstore)
            retriever = get_retriever(vectorstore)
            print(f"✅ {len(docs)} dokumen berhasil di-reindex.")
            continue

        # Retrieve relevant context
        try:
            relevant_docs = retriever.invoke(user_input)
        except Exception as e:
            print(f"❌ Error saat retrieval: {e}")
            continue

        if not relevant_docs:
            context_text = "(Tidak ada konteks yang relevan ditemukan)"
        else:
            context_text = "\n\n---\n\n".join(
                [f"📄 {doc.metadata.get('source', 'unknown')}:\n{doc.page_content}" for doc in relevant_docs]
            )

        # Build messages
        messages = [
            SystemMessage(content=SYSTEM_PROMPT_RAG),
            HumanMessage(content=(
                f"Konteks dari codebase:\n{context_text}\n\n"
                f"Pertanyaan user:\n{user_input}"
            )),
        ]

        # Get response
        try:
            response = llm.invoke(messages)
            print(f"\n🤖: {response.content}\n")
        except Exception as e:
            print(f"❌ Error dari LLM: {e}\n")


if __name__ == "__main__":
    main()