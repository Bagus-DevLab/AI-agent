"""
vectorstore.py — Modul untuk manajemen FAISS VectorStore.
Menangani pembuatan, update, dan penyimpanan vector database.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from config import CHUNK_SIZE, CHUNK_OVERLAP, RETRIEVER_TOP_K


def build_vectorstore(docs, embeddings):
    """
    Membangun FAISS VectorStore dari dokumen yang sudah di-load.
    
    Args:
        docs: List dokumen dari scanner
        embeddings: Instance HuggingFaceEmbeddings
        
    Returns:
        FAISS vectorstore instance, atau None jika gagal
    """
    if not docs:
        print("⚠️ Tidak ada dokumen untuk di-index.")
        return None

    # Split dokumen jadi chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(docs)
    print(f"✂️ Dokumen dipotong menjadi {len(chunks)} chunks.")

    # Bangun FAISS index
    print("🧠 Membangun vector database...")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    print("✅ Vector database siap!")

    return vectorstore


def get_retriever(vectorstore, top_k=None):
    """
    Membuat retriever dari vectorstore.
    
    Args:
        vectorstore: FAISS vectorstore instance
        top_k: Jumlah dokumen yang di-retrieve (default dari config)
        
    Returns:
        Retriever instance
    """
    k = top_k if top_k is not None else RETRIEVER_TOP_K
    return vectorstore.as_retriever(search_kwargs={"k": k})


def save_vectorstore(vectorstore, path="faiss_index"):
    """Simpan vectorstore ke disk agar tidak perlu rebuild."""
    vectorstore.save_local(path)
    print(f"💾 Vector database disimpan ke '{path}/'")


def load_vectorstore(embeddings, path="faiss_index"):
    """Load vectorstore dari disk."""
    try:
        vectorstore = FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)
        print(f"📂 Vector database di-load dari '{path}/'")
        return vectorstore
    except Exception:
        return None
