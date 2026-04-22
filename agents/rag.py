"""
agents/rag.py — Agent dengan RAG (Retrieval-Augmented Generation).
"""

import os
from langchain_core.messages import SystemMessage, HumanMessage
from config import get_llm, get_embeddings, SYSTEM_PROMPT_RAG, validate_config, BASE_DIR
from utils.scanner import scan_workspace
from utils.vectorstore import build_vectorstore, get_retriever, save_vectorstore, load_vectorstore
from utils.security import is_safe_path as _is_safe_path


def is_safe_path(path: str) -> bool:
    """Pastikan path berada di dalam BASE_DIR (security sandbox)."""
    return _is_safe_path(path, BASE_DIR)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _build_context(relevant_docs: list) -> str:
    """Format dokumen hasil retrieval menjadi string konteks."""
    if not relevant_docs:
        return "(Tidak ada konteks yang relevan ditemukan)"

    return "\n\n---\n\n".join(
        f"{doc.metadata.get('source', 'unknown')}:\n{doc.page_content}"
        for doc in relevant_docs
    )


def _init_vectorstore(embeddings) -> tuple:
    """Load atau buat vectorstore baru. Return (vectorstore, retriever)."""
    print("Memuat workspace...")
    vectorstore = load_vectorstore()

    if vectorstore is None:
        print("Membuat index baru...")
        docs, count = scan_workspace(BASE_DIR)
        if not docs:
            print("Tidak ada file yang ditemukan untuk di-index.")
            return None, None
        vectorstore = build_vectorstore(docs, embeddings)
        save_vectorstore(vectorstore)
        print(f"{count} dokumen berhasil di-index.")
    else:
        print("Index berhasil dimuat dari cache.")

    return vectorstore, get_retriever(vectorstore)


def _reindex(embeddings) -> tuple:
    """Rebuild vectorstore dari scratch. Return (vectorstore, retriever, docs)."""
    print("Rebuilding index...")
    docs, count = scan_workspace(BASE_DIR)
    if not docs:
        print("Tidak ada file yang ditemukan.")
        return None, None, []

    vectorstore = build_vectorstore(docs, embeddings)
    save_vectorstore(vectorstore)
    retriever = get_retriever(vectorstore)
    print(f"{len(docs)} dokumen berhasil di-reindex.")
    return vectorstore, retriever, docs


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(folder_path: str = ".") -> None:
    print("=== RAG AGENT ===\n")

    errors = validate_config()
    if errors:
        print("Konfigurasi tidak lengkap:")
        for err in errors:
            print(f"   - {err}")
        return

    llm = get_llm()
    embeddings = get_embeddings()

    vectorstore, retriever = _init_vectorstore(embeddings)
    if vectorstore is None:
        return

    print("\nAgent siap! Tanya apa saja tentang kode ini.")
    print("Ketik 'exit' untuk keluar, 'reindex' untuk rebuild index.\n")

    while True:
        try:
            user_input = input("Lu: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            break

        if not user_input:
            continue

        if user_input.lower() == "exit":
            print("Bye!")
            break

        if user_input.lower() == "reindex":
            vectorstore, retriever, _ = _reindex(embeddings)
            if vectorstore is None:
                continue
            continue

        # Retrieve & respond
        try:
            relevant_docs = retriever.invoke(user_input)
        except Exception as e:
            print(f"Error saat retrieval: {e}")
            continue

        context_text = _build_context(relevant_docs)
        messages = [
            SystemMessage(content=SYSTEM_PROMPT_RAG),
            HumanMessage(content=f"Konteks dari codebase:\n{context_text}\n\nPertanyaan user:\n{user_input}"),
        ]

        try:
            response = llm.invoke(messages)
            print(f"\nAI: {response.content}\n")
        except Exception as e:
            print(f"Error dari LLM: {e}\n")


if __name__ == "__main__":
    main()
