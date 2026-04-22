"""
utils/vectorstore.py — FAISS vector store helper untuk RAG.
"""

from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from config import get_embeddings, CHUNK_SIZE, CHUNK_OVERLAP, RETRIEVER_TOP_K


def build_vectorstore(file_list: list[dict], embeddings=None) -> FAISS:
    """
    Bangun FAISS vector store dari list file hasil scan.

    Args:
        file_list: List of dict dengan keys 'path' dan 'content'.
        embeddings: Optional embedding model (default dari config).
    """
    if not file_list:
        raise ValueError("Tidak ada file untuk di-index.")

    documents = [
        Document(
            page_content=f"// File Path: {f['path']}\n{f['content']}",
            metadata={"source": f["path"]},
        )
        for f in file_list
    ]

    print(f"   {len(documents)} file -> splitting chunks...")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\nclass ", "\ndef ", "\n\n", "\n", " "],
    )
    chunks = splitter.split_documents(documents)
    print(f"   {len(chunks)} chunks -> building embeddings...")

    try:
        emb_model = embeddings or get_embeddings()
        vectorstore = FAISS.from_documents(chunks, emb_model)
        print(f"   Vector store siap! ({len(chunks)} chunks indexed)")
        return vectorstore
    except Exception as e:
        raise RuntimeError(f"Gagal build vector store: {e}")


def save_vectorstore(vectorstore: FAISS, folder_path: str = "faiss_index") -> None:
    """Simpan vector store ke disk."""
    try:
        vectorstore.save_local(folder_path)
        print(f"   Vector store disimpan ke: {folder_path}")
    except Exception as e:
        print(f"   Gagal menyimpan vector store: {e}")


def load_vectorstore(folder_path: str = "faiss_index") -> FAISS | None:
    """Load vector store dari disk. Return None jika gagal."""
    try:
        embeddings = get_embeddings()
        return FAISS.load_local(
            folder_path,
            embeddings,
            allow_dangerous_deserialization=True,
        )
    except Exception as e:
        print(f"   Gagal memuat vector store: {e}")
        return None


def get_retriever(vectorstore: FAISS, top_k: int | None = None):
    """Buat retriever dari vector store."""
    k = top_k if top_k is not None else RETRIEVER_TOP_K
    return vectorstore.as_retriever(search_kwargs={"k": k})
